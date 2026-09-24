"""Importa todos los modelos para que SQLAlchemy los registre en Base.metadata.

El orden importa: las entidades referenciadas por claves foráneas deben
cargarse antes que las que las referencian.
"""
from app.models.rol import Permiso, Rol, rol_permisos  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.obra import Obra  # noqa: F401
from app.models.servicio import Servicio  # noqa: F401
from app.models.pedido import EstadoPedido, Pedido, TRANSICIONES_VALIDAS  # noqa: F401
from app.models.detalle_pedido import DetallePedido  # noqa: F401
from app.models.venta import (  # noqa: F401
    EstadoVenta,
    MetodoPago,
    TRANSICIONES_VENTA,
    Venta,
)
from app.models.detalle_venta import DetalleVenta  # noqa: F401
from app.models.factura import EstadoFactura, Factura, TRANSICIONES_FACTURA  # noqa: F401
from app.models.pago import EstadoPago, Pago  # noqa: F401
from app.models.pqr import PQR, EstadoPQR, TipoPQR, TRANSICIONES_PQR  # noqa: F401
from app.models.chat import Conversacion, Mensaje, RolMensaje  # noqa: F401

__all__ = [
    "Permiso", "Rol", "rol_permisos", "Usuario", "Obra", "Servicio",
    "Pedido", "EstadoPedido", "TRANSICIONES_VALIDAS", "DetallePedido",
    "Venta", "EstadoVenta", "MetodoPago", "TRANSICIONES_VENTA", "DetalleVenta",
    "Factura", "EstadoFactura", "TRANSICIONES_FACTURA", "Pago", "EstadoPago",
    "PQR", "EstadoPQR", "TipoPQR", "TRANSICIONES_PQR",
    "Conversacion", "Mensaje", "RolMensaje",
]
