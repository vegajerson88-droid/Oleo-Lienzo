"""Importa todos los modelos para que SQLAlchemy los registre en Base.metadata."""
from app.models.rol import Rol  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.obra import Obra  # noqa: F401
from app.models.servicio import Servicio  # noqa: F401
from app.models.pedido import Pedido, EstadoPedido, TRANSICIONES_VALIDAS  # noqa: F401
from app.models.detalle_pedido import DetallePedido  # noqa: F401
