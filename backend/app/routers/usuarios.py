"""Gestión de usuarios. Reservada al rol administrador."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import usuario as usuario_crud
from app.database import get_db
from app.dependencies.auth import get_current_user, solo_admin
from app.dependencies.common import (
    RESPUESTA_404,
    RESPUESTA_409,
    RESPUESTA_422,
    RESPUESTAS_AUTH,
    BuscarQuery,
    IdPath,
)
from app.dependencies.pagination import PaginationParams, pagination_params
from app.models.usuario import Usuario
from app.schemas.common import Page
from app.schemas.usuario import (
    RolOut,
    UsuarioAdminCreate,
    UsuarioEstadoUpdate,
    UsuarioOut,
    UsuarioReplace,
    UsuarioUpdate,
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"], responses=RESPUESTAS_AUTH)


@router.get(
    "",
    response_model=Page[UsuarioOut],
    summary="Listar usuarios",
    description=(
        "Devuelve los usuarios paginados. Admite filtrar por rol y por estado, "
        "y buscar por nombre, apellido, correo o documento.\n\n"
        "La respuesta nunca incluye el hash de la contraseña."
    ),
)
async def listar_usuarios(
    rol: str | None = Query(default=None, description="administrador, empleado o cliente."),
    activo: bool | None = Query(default=None, description="Filtra por estado."),
    buscar: BuscarQuery = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(solo_admin),
):
    items, total = await usuario_crud.list_usuarios(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        rol_nombre=rol,
        activo=activo,
        buscar=buscar,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get(
    "/roles",
    response_model=list[RolOut],
    summary="Listar roles y sus permisos",
    description="Catálogo de roles con los permisos asignados a cada uno.",
)
async def listar_roles(
    db: AsyncSession = Depends(get_db), _admin: Usuario = Depends(solo_admin)
):
    return await usuario_crud.list_roles(db)


@router.get(
    "/{usuario_id}",
    response_model=UsuarioOut,
    summary="Consultar un usuario",
    responses=RESPUESTA_404,
)
async def obtener_usuario(
    usuario_id: IdPath,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(solo_admin),
):
    try:
        return await usuario_crud.get_by_id(db, usuario_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post(
    "",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un usuario desde el panel",
    description=(
        "Alta manual de usuarios. A diferencia del registro público, aquí el "
        "administrador elige el rol (`rol_nombre`), por ejemplo para dar de "
        "alta a un empleado."
    ),
    responses={**RESPUESTA_409, **RESPUESTA_422},
)
async def crear_usuario(
    data: UsuarioAdminCreate,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(solo_admin),
):
    try:
        return await usuario_crud.create_usuario(db, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.put(
    "/{usuario_id}",
    response_model=UsuarioOut,
    summary="Reemplazar un usuario (actualización completa)",
    description=(
        "**PUT**: sustituye por completo los datos modificables del usuario. "
        "Hay que enviar todos los campos; omitir uno es un error de "
        "validación, no una señal de «déjalo como está».\n\n"
        "Para cambiar solo un campo, usa `PATCH`."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def reemplazar_usuario(
    usuario_id: IdPath,
    data: UsuarioReplace,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(solo_admin),
):
    try:
        return await usuario_crud.replace_usuario(db, usuario_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioOut,
    summary="Actualizar un usuario (parcialmente)",
    description="**PATCH**: modifica únicamente los campos incluidos en el cuerpo.",
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def actualizar_usuario(
    usuario_id: IdPath,
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(solo_admin),
):
    try:
        return await usuario_crud.update_usuario(db, usuario_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch(
    "/{usuario_id}/estado",
    response_model=UsuarioOut,
    summary="Activar o desactivar un usuario",
    description=(
        "Cambia el estado sin borrar el registro. Es la vía recomendada frente "
        "al borrado físico: conserva el historial de pedidos, ventas y facturas "
        "del usuario.\n\n"
        "Un usuario inactivo no puede iniciar sesión (recibe un 403)."
    ),
    responses=RESPUESTA_404,
)
async def cambiar_estado_usuario(
    usuario_id: IdPath,
    data: UsuarioEstadoUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(solo_admin),
):
    if usuario_id == admin.id and not data.activo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No puedes desactivar tu propia cuenta.",
        )
    try:
        return await usuario_crud.cambiar_estado(db, usuario_id, data.activo)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un usuario",
    description=(
        "Borrado físico. Falla con 409 si el usuario tiene pedidos, ventas o "
        "facturas asociadas: en ese caso hay que desactivarlo con "
        "`PATCH /usuarios/{id}/estado` para no romper el historial."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_409},
)
async def eliminar_usuario(
    usuario_id: IdPath,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(solo_admin),
):
    if usuario_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No puedes eliminar tu propia cuenta.",
        )
    try:
        await usuario_crud.delete_usuario(db, usuario_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
