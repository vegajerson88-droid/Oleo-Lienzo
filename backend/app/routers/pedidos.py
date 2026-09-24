from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import pedido as pedido_crud
from app.database import AsyncSessionLocal, get_db
from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.pagination import PaginationParams, pagination_params
from app.models.pedido import EstadoPedido
from app.models.usuario import Usuario
from app.schemas.common import Page
from app.schemas.pedido import PedidoCambioEstado, PedidoCreate, PedidoOut

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


async def _notificar_cambio_estado(pedido_id: int, nuevo_estado: str) -> None:
    try:
        async with AsyncSessionLocal():
            print(f"[NOTIFICACIÓN] pedido_id={pedido_id} nuevo_estado={nuevo_estado}")
    except Exception as exc:
        print(f"[NOTIFICACIÓN][ERROR] {exc}")


@router.get("", response_model=Page[PedidoOut])
async def listar_pedidos(
    estado: EstadoPedido | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    # cliente solo ve los suyos; administrador/empleado ven todos
    cliente_id = usuario.id if usuario.rol.nombre == "cliente" else None
    items, total = await pedido_crud.list_pedidos(
        db, page=pagination.page, page_size=pagination.page_size,
        cliente_id=cliente_id, estado=estado,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{pedido_id}", response_model=PedidoOut)
async def obtener_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        pedido = await pedido_crud.get_by_id(db, pedido_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    if usuario.rol.nombre == "cliente" and pedido.cliente_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No es tu pedido.")
    return pedido


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
async def crear_pedido(
    data: PedidoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_roles("cliente")),
):
    try:
        return await pedido_crud.create_pedido(db, usuario.id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch("/{pedido_id}/estado", response_model=PedidoOut)
async def cambiar_estado_pedido(
    pedido_id: int,
    data: PedidoCambioEstado,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _u=Depends(require_roles("administrador", "empleado")),
):
    """Sub-recurso de negocio (no CRUD puro): transición de estado del pedido."""
    try:
        pedido = await pedido_crud.cambiar_estado(db, pedido_id, data.nuevo_estado)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    background_tasks.add_task(_notificar_cambio_estado, pedido.id, pedido.estado.value)
    return pedido
