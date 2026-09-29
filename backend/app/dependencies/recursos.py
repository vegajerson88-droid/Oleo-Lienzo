"""Dependencias que resuelven el recurso nombrado en la ruta.

En lugar de que cada operación repita «búscalo y, si no está, 404», la ruta
declara el recurso que necesita y lo recibe ya cargado. Si no existe, la
dependencia corta antes de entrar en la función: el cuerpo del endpoint solo
se ejecuta cuando el recurso está garantizado.

El 404 lo produce el `NotFoundError` que lanza la capa `crud`, que el
manejador registrado en `main.py` traduce al código y al formato de la API.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import factura as factura_crud
from app.crud import obra as obra_crud
from app.crud import pqr as pqr_crud
from app.crud import servicio as servicio_crud
from app.crud import venta as venta_crud
from app.database import get_db
from app.dependencies.common import IdPath
from app.models.factura import Factura
from app.models.obra import Obra
from app.models.pqr import PQR
from app.models.servicio import Servicio
from app.models.venta import Venta


async def obra_de_la_ruta(obra_id: IdPath, db: AsyncSession = Depends(get_db)) -> Obra:
    """La obra de `{obra_id}`, o 404 si no existe."""
    return await obra_crud.get_by_id(db, obra_id)


async def servicio_de_la_ruta(servicio_id: IdPath, db: AsyncSession = Depends(get_db)) -> Servicio:
    """El servicio de `{servicio_id}`, o 404 si no existe."""
    return await servicio_crud.get_by_id(db, servicio_id)


async def venta_de_la_ruta(venta_id: IdPath, db: AsyncSession = Depends(get_db)) -> Venta:
    """La venta de `{venta_id}`, o 404 si no existe."""
    return await venta_crud.get_by_id(db, venta_id)


async def factura_de_la_ruta(factura_id: IdPath, db: AsyncSession = Depends(get_db)) -> Factura:
    """La factura de `{factura_id}`, o 404 si no existe."""
    return await factura_crud.get_by_id(db, factura_id)


async def pqr_de_la_ruta(pqr_id: IdPath, db: AsyncSession = Depends(get_db)) -> PQR:
    """La PQR de `{pqr_id}`, o 404 si no existe."""
    return await pqr_crud.get_by_id(db, pqr_id)
