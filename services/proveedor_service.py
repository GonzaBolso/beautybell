from repository.proveedor_repo import ProveedorRepo
from repository.producto_repo import ProductoRepo
from repository.compra_repo import CompraRepo
from repository.caja_repo import CajaRepo


class ProveedorService:
    """Lógica de negocio para proveedores y sus productos."""

    def __init__(self):
        self._repo = ProveedorRepo()
        self._prod_repo = ProductoRepo()

    def obtener_todos(self) -> list:
        return self._repo.obtener_todos()

    def obtener_por_id(self, id: int):
        return self._repo.obtener_por_id(id)

    def buscar(self, texto: str) -> list:
        return self._repo.buscar(texto)

    def crear(self, nombre: str, telefono: str = "", email: str = "",
              direccion: str = "", notas: str = "") -> tuple[bool, str, int | None]:
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre no puede estar vacío.", None
        id_ = self._repo.crear(nombre, telefono, email, direccion, notas)
        return True, "Proveedor creado correctamente.", id_

    def actualizar(self, id: int, nombre: str, telefono: str, email: str,
                   direccion: str, notas: str) -> tuple[bool, str]:
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre no puede estar vacío."
        self._repo.actualizar(id, nombre, telefono, email, direccion, notas)
        return True, "Proveedor actualizado correctamente."

    def eliminar(self, id: int):
        self._repo.eliminar(id)

    # Productos del proveedor
    def obtener_productos(self, proveedor_id: int) -> list:
        return self._prod_repo.obtener_por_proveedor(proveedor_id)

    def crear_producto(self, nombre: str, proveedor_id: int = None, categoria: str = "",
                       precio_costo: float = 0, precio_venta: float = 0,
                       stock: int = 0) -> tuple[bool, str, int | None]:
        if not nombre.strip():
            return False, "El nombre del producto no puede estar vacío.", None
        id_ = self._prod_repo.crear(nombre.strip(), proveedor_id, categoria,
                                    precio_costo, precio_venta, stock)
        return True, "Producto creado correctamente.", id_

    def actualizar_producto(self, id: int, nombre: str, proveedor_id: int, categoria: str,
                            precio_costo: float, precio_venta: float,
                            stock: int) -> tuple[bool, str]:
        if not nombre.strip():
            return False, "El nombre del producto no puede estar vacío."
        self._prod_repo.actualizar(id, nombre.strip(), proveedor_id, categoria,
                                   precio_costo, precio_venta, stock)
        return True, "Producto actualizado correctamente."


class CompraService:
    """
    Registra una compra a proveedor:
    1. Crea la cabecera en compras_proveedor
    2. Agrega el detalle (productos, cantidades, precios)
    3. Ajusta el stock de cada producto
    4. Registra el egreso en caja automáticamente
    """

    def __init__(self):
        self._compra_repo = CompraRepo()
        self._prod_repo   = ProductoRepo()
        self._caja_repo   = CajaRepo()

    def registrar_compra(self, proveedor_id: int, metodo_pago_id: int,
                         items: list[dict], notas: str = "",
                         fecha: str = None) -> tuple[bool, str, int | None]:
        """
        items: [{ 'producto_id': int, 'cantidad': int, 'precio_unitario': float }, ...]
        """
        if not items:
            return False, "La compra debe tener al menos un producto.", None

        total = sum(i["cantidad"] * i["precio_unitario"] for i in items)
        if total <= 0:
            return False, "El total de la compra debe ser mayor a cero.", None

        compra_id = self._compra_repo.crear_cabecera(
            proveedor_id=proveedor_id,
            metodo_pago_id=metodo_pago_id,
            total=total,
            fecha=fecha,
            notas=notas,
        )

        for item in items:
            self._compra_repo.agregar_detalle(
                compra_id=compra_id,
                producto_id=item["producto_id"],
                cantidad=item["cantidad"],
                precio_unitario=item["precio_unitario"],
            )
            self._prod_repo.ajustar_stock(item["producto_id"], item["cantidad"])

        self._caja_repo.registrar(
            tipo="egreso",
            categoria="Compra a proveedor",
            monto=total,
            metodo_pago_id=metodo_pago_id,
            descripcion=f"Compra #{compra_id}" + (f" — {notas}" if notas else ""),
            proveedor_id=proveedor_id,
        )

        return True, f"Compra registrada por ${total:,.2f}.", compra_id

    def obtener_todas(self) -> list:
        return self._compra_repo.obtener_todas()

    def obtener_detalle(self, compra_id: int) -> list:
        return self._compra_repo.obtener_detalle(compra_id)