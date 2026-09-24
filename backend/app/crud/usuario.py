"""Operaciones de base de datos sobre usuarios, roles y permisos."""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.crud.base import borrar_protegido, contar, paginar
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioAdminCreate,
    UsuarioCreate,
    UsuarioReplace,
    UsuarioUpdate,
)

# Carga el rol y sus permisos en la misma consulta: evita N+1 al autorizar.
_CON_ROL = selectinload(Usuario.rol).selectinload(Rol.permisos)


async def get_rol_by_nombre(db: AsyncSession, nombre: str) -> Rol | None:
    return (await db.execute(select(Rol).where(Rol.nombre == nombre))).scalar_one_or_none()


async def list_roles(db: AsyncSession) -> list[Rol]:
    return list((await db.execute(select(Rol).order_by(Rol.id))).scalars().all())


async def get_by_email(db: AsyncSession, email: str) -> Usuario | None:
    query = select(Usuario).where(Usuario.email == email.lower()).options(_CON_ROL)
    return (await db.execute(query)).scalar_one_or_none()


async def get_by_id(db: AsyncSession, usuario_id: int) -> Usuario:
    query = select(Usuario).where(Usuario.id == usuario_id).options(_CON_ROL)
    usuario = (await db.execute(query)).scalar_one_or_none()
    if not usuario:
        raise NotFoundError(f"Usuario {usuario_id} no encontrado.")
    return usuario


async def list_usuarios(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    rol_nombre: str | None = None,
    activo: bool | None = None,
    buscar: str | None = None,
) -> tuple[list[Usuario], int]:
    query = select(Usuario).options(_CON_ROL)
    if rol_nombre:
        query = query.join(Rol).where(Rol.nombre == rol_nombre)
    if activo is not None:
        query = query.where(Usuario.activo == activo)
    if buscar:
        patron = f"%{buscar}%"
        query = query.where(
            or_(
                Usuario.nombre.ilike(patron),
                Usuario.apellido.ilike(patron),
                Usuario.email.ilike(patron),
                Usuario.numero_documento.ilike(patron),
            )
        )
    total = await contar(db, query)
    query = paginar(query.order_by(Usuario.id.desc()), page, page_size)
    return list((await db.execute(query)).scalars().unique().all()), total


async def _verificar_unicidad(
    db: AsyncSession, email: str, numero_documento: str
) -> None:
    """Un correo y un documento no pueden repetirse: responde 409 si ya existen."""
    if await get_by_email(db, email):
        raise ConflictError("Ya existe un usuario registrado con ese correo.")
    existente = await db.execute(
        select(Usuario).where(Usuario.numero_documento == numero_documento)
    )
    if existente.scalar_one_or_none():
        raise ConflictError("Ya existe un usuario registrado con ese número de documento.")


async def create_usuario(
    db: AsyncSession,
    data: UsuarioCreate | UsuarioAdminCreate,
    rol_nombre: str = "cliente",
) -> Usuario:
    await _verificar_unicidad(db, data.email, data.numero_documento)

    nombre_rol = getattr(data, "rol_nombre", None) or rol_nombre
    rol = await get_rol_by_nombre(db, nombre_rol)
    if not rol:
        raise NotFoundError(f"El rol '{nombre_rol}' no existe. Ejecuta el seed primero.")

    usuario = Usuario(
        nombre=data.nombre,
        apellido=data.apellido,
        tipo_documento=data.tipo_documento,
        numero_documento=data.numero_documento,
        direccion=data.direccion,
        telefono=data.telefono,
        email=data.email,
        password_hash=hash_password(data.password),
        rol_id=rol.id,
    )
    db.add(usuario)
    await db.commit()
    return await get_by_id(db, usuario.id)


async def _validar_rol(db: AsyncSession, rol_id: int) -> None:
    if not await db.get(Rol, rol_id):
        raise NotFoundError(f"El rol {rol_id} no existe.")


async def replace_usuario(db: AsyncSession, usuario_id: int, data: UsuarioReplace) -> Usuario:
    """PUT: reemplaza los datos modificables del usuario."""
    usuario = await get_by_id(db, usuario_id)
    await _validar_rol(db, data.rol_id)
    for field, value in data.model_dump().items():
        setattr(usuario, field, value)
    await db.commit()
    return await get_by_id(db, usuario_id)


async def update_usuario(db: AsyncSession, usuario_id: int, data: UsuarioUpdate) -> Usuario:
    """PATCH: modifica solo los campos enviados."""
    usuario = await get_by_id(db, usuario_id)
    cambios = data.model_dump(exclude_unset=True)
    if "rol_id" in cambios and cambios["rol_id"] is not None:
        await _validar_rol(db, cambios["rol_id"])
    for field, value in cambios.items():
        setattr(usuario, field, value)
    await db.commit()
    return await get_by_id(db, usuario_id)


async def cambiar_estado(db: AsyncSession, usuario_id: int, activo: bool) -> Usuario:
    """Activa o desactiva un usuario conservando su historial."""
    usuario = await get_by_id(db, usuario_id)
    usuario.activo = activo
    await db.commit()
    return await get_by_id(db, usuario_id)


async def actualizar_password(db: AsyncSession, usuario: Usuario, password_plano: str) -> None:
    usuario.password_hash = hash_password(password_plano)
    await db.commit()


async def delete_usuario(db: AsyncSession, usuario_id: int) -> None:
    usuario = await get_by_id(db, usuario_id)
    await borrar_protegido(db, usuario, f"el usuario {usuario.email}")
