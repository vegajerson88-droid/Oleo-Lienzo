from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


async def get_rol_by_nombre(db: AsyncSession, nombre: str) -> Rol | None:
    result = await db.execute(select(Rol).where(Rol.nombre == nombre))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> Usuario | None:
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, usuario_id: int) -> Usuario:
    usuario = await db.get(Usuario, usuario_id)
    if not usuario:
        raise NotFoundError(f"Usuario {usuario_id} no encontrado.")
    return usuario


async def list_usuarios(
    db: AsyncSession, page: int = 1, page_size: int = 10, rol_nombre: str | None = None
) -> tuple[list[Usuario], int]:
    query = select(Usuario)
    if rol_nombre:
        query = query.join(Rol).where(Rol.nombre == rol_nombre)
    total = len((await db.execute(query)).scalars().all())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_usuario(db: AsyncSession, data: UsuarioCreate, rol_nombre: str = "cliente") -> Usuario:
    if await get_by_email(db, data.email):
        raise ConflictError("Ya existe un usuario registrado con ese correo.")

    existing_doc = await db.execute(
        select(Usuario).where(Usuario.numero_documento == data.numero_documento)
    )
    if existing_doc.scalar_one_or_none():
        raise ConflictError("Ya existe un usuario registrado con ese número de documento.")

    rol = await get_rol_by_nombre(db, rol_nombre)
    if not rol:
        raise NotFoundError(f"El rol '{rol_nombre}' no existe. Ejecuta el seed primero.")

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
    await db.refresh(usuario, attribute_names=["rol"])
    return usuario


async def update_usuario(db: AsyncSession, usuario_id: int, data: UsuarioUpdate) -> Usuario:
    usuario = await get_by_id(db, usuario_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(usuario, field, value)
    await db.commit()
    await db.refresh(usuario, attribute_names=["rol"])
    return usuario


async def delete_usuario(db: AsyncSession, usuario_id: int) -> None:
    usuario = await get_by_id(db, usuario_id)
    await db.delete(usuario)
    await db.commit()
