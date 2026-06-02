from repository.servicio_repo import ServicioRepo
from repository.empleada_repo import EmpleadaRepo
from repository.metodo_pago_repo import MetodoPagoRepo


class ConfiguracionService:
    """
    Administra las entidades de configuración del negocio:
    servicios ofrecidos, empleadas y métodos de pago.
    Se accede desde la pantalla de Configuración de la app.
    """

    def __init__(self):
        self._servicio_repo    = ServicioRepo()
        self._empleada_repo    = EmpleadaRepo()
        self._metodo_pago_repo = MetodoPagoRepo()

    # ------------------------------------------------------------------ #
    #  Servicios                                                           #
    # ------------------------------------------------------------------ #

    def obtener_servicios(self) -> list:
        return self._servicio_repo.obtener_todos()

    def obtener_categorias_servicios(self) -> list[str]:
        """Lista de categorías únicas ya existentes en la tabla."""
        return self._servicio_repo.obtener_categorias()

    def crear_servicio(self, nombre: str, categoria: str, precio: float,
                       duracion_min: int = 60) -> tuple[bool, str, int | None]:
        if not nombre.strip():
            return False, "El nombre no puede estar vacío.", None
        if precio < 0:
            return False, "El precio no puede ser negativo.", None
        id_ = self._servicio_repo.crear(
            nombre.strip(), categoria.strip(), precio, duracion_min
        )
        return True, "Servicio creado correctamente.", id_

    def actualizar_servicio(self, id: int, nombre: str, categoria: str,
                            precio: float, duracion_min: int,
                            activo: bool) -> tuple[bool, str]:
        if not nombre.strip():
            return False, "El nombre no puede estar vacío."
        if precio < 0:
            return False, "El precio no puede ser negativo."
        self._servicio_repo.actualizar(
            id, nombre.strip(), categoria.strip(), precio, duracion_min, activo
        )
        return True, "Servicio actualizado correctamente."

    def eliminar_servicio(self, id: int):
        self._servicio_repo.eliminar(id)

    # ------------------------------------------------------------------ #
    #  Empleadas                                                           #
    # ------------------------------------------------------------------ #

    def obtener_empleadas(self) -> list:
        return self._empleada_repo.obtener_todas()

    def crear_empleada(self, nombre: str, telefono: str = "") -> tuple[bool, str, int | None]:
        if not nombre.strip():
            return False, "El nombre no puede estar vacío.", None
        id_ = self._empleada_repo.crear(nombre.strip(), telefono.strip())
        return True, "Empleada creada correctamente.", id_

    def actualizar_empleada(self, id: int, nombre: str,
                            telefono: str, activa: bool) -> tuple[bool, str]:
        if not nombre.strip():
            return False, "El nombre no puede estar vacío."
        self._empleada_repo.actualizar(id, nombre.strip(), telefono.strip(), activa)
        return True, "Empleada actualizada correctamente."

    # ------------------------------------------------------------------ #
    #  Métodos de pago                                                     #
    # ------------------------------------------------------------------ #

    def obtener_metodos_pago(self) -> list:
        return self._metodo_pago_repo.obtener_todos()

    def crear_metodo_pago(self, nombre: str) -> tuple[bool, str, int | None]:
        if not nombre.strip():
            return False, "El nombre no puede estar vacío.", None
        id_ = self._metodo_pago_repo.crear(nombre.strip())
        return True, "Método de pago creado correctamente.", id_

    def actualizar_metodo_pago(self, id: int, nombre: str,
                               activo: bool) -> tuple[bool, str]:
        if not nombre.strip():
            return False, "El nombre no puede estar vacío."
        self._metodo_pago_repo.actualizar(id, nombre.strip(), activo)
        return True, "Método de pago actualizado correctamente."

    def eliminar_metodo_pago(self, id: int):
        self._metodo_pago_repo.eliminar(id)