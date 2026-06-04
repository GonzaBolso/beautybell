from datetime import datetime
from repository.turno_repo import TurnoRepo
from repository.servicio_repo import ServicioRepo


class TurnoService:

    ESTADOS = ["pendiente", "confirmado", "completado", "cancelado"]

    def __init__(self):
        self._repo = TurnoRepo()
        self._servicio_repo = ServicioRepo()

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    def obtener_por_fecha(self, fecha: str) -> list:
        return self._repo.obtener_por_fecha(fecha)

    def obtener_por_rango(self, fecha_desde: str, fecha_hasta: str) -> list:
        return self._repo.obtener_por_rango(fecha_desde, fecha_hasta)

    def obtener_por_id(self, id: int):
        return self._repo.obtener_por_id(id)

    def obtener_hoy(self) -> list:
        hoy = datetime.now().strftime("%Y-%m-%d")
        return self._repo.obtener_por_fecha(hoy)

    # ------------------------------------------------------------------ #
    #  Crear / editar                                                      #
    # ------------------------------------------------------------------ #

    def crear(self, cliente_id: int, empleada_id: int,
              servicios: list,           # [{servicio_id, precio}, ...]
              fecha_hora: str, notas: str = "",
              forzar: bool = False) -> tuple[bool, str, int | None]:
        """
        servicios: lista de dicts {servicio_id, precio}.
        El primer servicio se usa como referencia para la duracion en la validacion.
        """
        if not servicios:
            return False, "Debes agregar al menos un servicio.", None

        primer_srv_id = servicios[0]["servicio_id"]
        ok, msg, solapamiento = self._validar(empleada_id, primer_srv_id, fecha_hora)
        if not ok:
            if solapamiento and not forzar:
                return False, msg, -1
            elif solapamiento and forzar:
                pass
            else:
                return False, msg, None

        turno_id = self._repo.crear(
            cliente_id=cliente_id,
            empleada_id=empleada_id,
            servicio_id=primer_srv_id,   # campo legacy
            fecha_hora=fecha_hora,
            notas=notas
        )
        self._repo.guardar_servicios(turno_id, servicios)
        return True, "Turno creado correctamente.", turno_id

    def actualizar(self, id: int, cliente_id: int, empleada_id: int,
                   servicios: list,       # [{servicio_id, precio}, ...]
                   fecha_hora: str, estado: str, notas: str = "",
                   forzar: bool = False) -> tuple[bool, str]:
        if estado not in self.ESTADOS:
            return False, f"Estado inválido: {estado}"
        if not servicios:
            return False, "Debes agregar al menos un servicio."

        primer_srv_id = servicios[0]["servicio_id"]
        ok, msg, solapamiento = self._validar(empleada_id, primer_srv_id, fecha_hora, excluir_id=id)
        if not ok:
            if solapamiento and not forzar:
                return False, msg
            elif not solapamiento:
                return False, msg

        self._repo.actualizar(id, cliente_id, empleada_id, primer_srv_id, fecha_hora, estado, notas)
        self._repo.guardar_servicios(id, servicios)
        return True, "Turno actualizado correctamente."

    def cambiar_estado(self, id: int, estado: str) -> tuple[bool, str]:
        if estado not in self.ESTADOS:
            return False, f"Estado inválido: {estado}"
        self._repo.actualizar_estado(id, estado)
        return True, f"Estado actualizado a '{estado}'."

    def cancelar(self, id: int) -> tuple[bool, str]:
        return self.cambiar_estado(id, "cancelado")

    def completar(self, id: int) -> tuple[bool, str]:
        return self.cambiar_estado(id, "completado")

    def eliminar(self, id: int):
        self._repo.eliminar(id)

    # ------------------------------------------------------------------ #
    #  Validaciones internas                                               #
    # ------------------------------------------------------------------ #

    def _validar(self, empleada_id: int, servicio_id: int,
                 fecha_hora: str, excluir_id: int = None) -> tuple[bool, str, bool]:
        try:
            datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M")
        except ValueError:
            return False, "Formato de fecha inválido. Usar 'YYYY-MM-DD HH:MM'.", False

        servicio = self._servicio_repo.obtener_por_id(servicio_id)
        if not servicio:
            return False, "El servicio seleccionado no existe.", False

        duracion = servicio["duracion_min"]

        solapados = self._repo.obtener_solapados(
            empleada_id=empleada_id,
            fecha_hora=fecha_hora,
            duracion_min=duracion,
            excluir_id=excluir_id
        )
        if solapados:
            conflicto = solapados[0]
            return False, (
                f"Ya hay un turno a las {conflicto['fecha_hora'][11:16]}. "
                f"¿Querés agendarlo igual?"
            ), True

        return True, "", False