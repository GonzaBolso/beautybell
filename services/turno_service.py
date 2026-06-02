from datetime import datetime
from repository.turno_repo import TurnoRepo
from repository.servicio_repo import ServicioRepo


class TurnoService:
    """
    Lógica de negocio para turnos.
    Valida conflictos de horario, estados y reglas del negocio.
    La UI nunca toca el repo directamente.
    """

    ESTADOS = ["pendiente", "confirmado", "completado", "cancelado"]

    def __init__(self):
        self._repo = TurnoRepo()
        self._servicio_repo = ServicioRepo()

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    def obtener_por_fecha(self, fecha: str) -> list:
        """fecha: 'YYYY-MM-DD'"""
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

    def crear(self, cliente_id: int, empleada_id: int, servicio_id: int,
              fecha_hora: str, notas: str = "",
              forzar: bool = False) -> tuple[bool, str, int | None]:
        """
        Retorna (ok, mensaje, turno_id).
        - ok=True  → turno creado.
        - ok=False, turno_id=None → error de validación duro (fecha inválida, etc).
        - ok=False, turno_id=-1  → hay solapamiento pero se puede forzar.
          La UI debe preguntar al usuario y reintentar con forzar=True.
        """
        ok, msg, solapamiento = self._validar(empleada_id, servicio_id, fecha_hora)
        if not ok:
            if solapamiento and not forzar:
                return False, msg, -1   # -1 = señal de "preguntar al usuario"
            elif solapamiento and forzar:
                pass                    # el usuario confirmó, seguimos igual
            else:
                return False, msg, None # error duro, no se puede forzar

        turno_id = self._repo.crear(
            cliente_id=cliente_id,
            empleada_id=empleada_id,
            servicio_id=servicio_id,
            fecha_hora=fecha_hora,
            notas=notas
        )
        return True, "Turno creado correctamente.", turno_id

    def actualizar(self, id: int, cliente_id: int, empleada_id: int, servicio_id: int,
                   fecha_hora: str, estado: str, notas: str = "",
                   forzar: bool = False) -> tuple[bool, str]:
        if estado not in self.ESTADOS:
            return False, f"Estado inválido: {estado}"

        ok, msg, solapamiento = self._validar(empleada_id, servicio_id, fecha_hora, excluir_id=id)
        if not ok:
            if solapamiento and not forzar:
                return False, msg       # la UI pregunta y reintenta con forzar=True
            elif not solapamiento:
                return False, msg

        self._repo.actualizar(id, cliente_id, empleada_id, servicio_id, fecha_hora, estado, notas)
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
        """Retorna (ok, mensaje, es_solapamiento)."""

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

    # ------------------------------------------------------------------ #
    #  Helpers para la UI                                                  #
    # ------------------------------------------------------------------ #

    def horarios_disponibles(self, fecha: str, empleada_id: int,
                             duracion_min: int, hora_inicio: str = "09:00",
                             hora_fin: str = "20:00", intervalo_min: int = 30) -> list[str]:
        """
        Devuelve lista de horarios libres en formato 'HH:MM' para una fecha y empleada.
        Útil para mostrar un selector de horas en la UI.
        """
        from datetime import timedelta

        turnos_del_dia = self._repo.obtener_por_fecha(fecha)
        ocupados = [
            (t["fecha_hora"][11:16], t["duracion_min"] if "duracion_min" in t.keys() else 60)
            for t in turnos_del_dia
            if t["empleada_id"] == empleada_id and t["estado"] != "cancelado"
        ]

        inicio = datetime.strptime(f"{fecha} {hora_inicio}", "%Y-%m-%d %H:%M")
        fin    = datetime.strptime(f"{fecha} {hora_fin}",    "%Y-%m-%d %H:%M")
        delta  = timedelta(minutes=intervalo_min)

        libres = []
        slot = inicio
        while slot + timedelta(minutes=duracion_min) <= fin:
            hora_str = slot.strftime("%H:%M")
            slot_fin = slot + timedelta(minutes=duracion_min)

            solapado = False
            for hora_oc, dur_oc in ocupados:
                oc_inicio = datetime.strptime(f"{fecha} {hora_oc}", "%Y-%m-%d %H:%M")
                oc_fin    = oc_inicio + timedelta(minutes=dur_oc)
                if slot < oc_fin and slot_fin > oc_inicio:
                    solapado = True
                    break

            if not solapado:
                libres.append(hora_str)
            slot += delta

        return libres