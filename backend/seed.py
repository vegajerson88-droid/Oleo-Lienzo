"""Puebla la base de datos con datos de prueba razonables.

Uso: python seed.py
"""
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database import AsyncSessionLocal, init_models
from app.models.obra import Obra
from app.models.rol import Rol
from app.models.servicio import Servicio
from app.models.usuario import Usuario
from app.services.ai_local import entrenar_y_guardar

ROLES = ["administrador", "empleado", "cliente"]

OBRAS = [
    {"titulo": "Amanecer en el Valle", "artista": "Marina Solórzano", "anio": 2021,
     "tecnica": "Óleo sobre lienzo", "precio": 1250000,
     "descripcion": "Pinceladas cálidas que capturan la luz del primer sol sobre un valle en calma."},
    {"titulo": "Fragmentos Azules", "artista": "Iván Restrepo", "anio": 2019,
     "tecnica": "Acrílico sobre lienzo", "precio": 980000,
     "descripcion": "Una composición geométrica que descompone el horizonte en planos de azul profundo."},
    {"titulo": "Tormenta Interior", "artista": "Camila Duarte", "anio": 2022,
     "tecnica": "Óleo sobre lienzo", "precio": 1480000,
     "descripcion": "Trazos densos y oscuros que expresan la tensión emocional de una tormenta contenida."},
    {"titulo": "Jardín Silencioso", "artista": "Marina Solórzano", "anio": 2020,
     "tecnica": "Acrílico sobre lienzo", "precio": 890000,
     "descripcion": "Formas orgánicas en tonos verdes que evocan la quietud de un jardín al amanecer."},
    {"titulo": "Geometría del Deseo", "artista": "Tomás Aguilar", "anio": 2023,
     "tecnica": "Óleo sobre lienzo", "precio": 1650000,
     "descripcion": "Bloques rotundos en rojo y negro que juegan con el equilibrio y la tensión visual."},
    {"titulo": "Ecos de Otoño", "artista": "Camila Duarte", "anio": 2018,
     "tecnica": "Óleo sobre lienzo", "precio": 1020000,
     "descripcion": "Capas cálidas de ocre y siena que rememoran la caída de las hojas en octubre."},
]

SERVICIOS = [
    {"nombre": "Enmarcado personalizado", "descripcion": "Enmarcado a medida para obras adquiridas.",
     "precio": 150000},
    {"nombre": "Restauración básica", "descripcion": "Limpieza y restauración leve de obras.",
     "precio": 300000},
    {"nombre": "Envío asegurado", "descripcion": "Transporte de la obra con seguro incluido.",
     "precio": 90000},
]

USUARIOS = [
    {"nombre": "Ana", "apellido": "Restrepo", "tipo_documento": "CC", "numero_documento": "1000000001",
     "direccion": "Calle 10 # 20-30", "telefono": "3001234567", "email": "admin@oleoylienzo.com",
     "password": "Admin1234", "rol": "administrador"},
    {"nombre": "Luis", "apellido": "Gómez", "tipo_documento": "CC", "numero_documento": "1000000002",
     "direccion": "Carrera 45 # 12-05", "telefono": "3007654321", "email": "empleado@oleoylienzo.com",
     "password": "Empleado123", "rol": "empleado"},
    {"nombre": "Sara", "apellido": "Pérez", "tipo_documento": "CC", "numero_documento": "1000000003",
     "direccion": "Avenida Siempre Viva 742", "telefono": "3009876543", "email": "cliente@oleoylienzo.com",
     "password": "Cliente123", "rol": "cliente"},
]


async def seed() -> None:
    await init_models()
    async with AsyncSessionLocal() as db:
        roles_by_name = {}
        for nombre in ROLES:
            existente = (await db.execute(select(Rol).where(Rol.nombre == nombre))).scalar_one_or_none()
            if not existente:
                existente = Rol(nombre=nombre)
                db.add(existente)
                await db.flush()
            roles_by_name[nombre] = existente
        await db.commit()

        for u in USUARIOS:
            existente = (await db.execute(select(Usuario).where(Usuario.email == u["email"]))).scalar_one_or_none()
            if existente:
                continue
            db.add(Usuario(
                nombre=u["nombre"], apellido=u["apellido"], tipo_documento=u["tipo_documento"],
                numero_documento=u["numero_documento"], direccion=u["direccion"], telefono=u["telefono"],
                email=u["email"], password_hash=hash_password(u["password"]),
                rol_id=roles_by_name[u["rol"]].id,
            ))
        await db.commit()

        if (await db.execute(select(Obra))).scalars().first() is None:
            for o in OBRAS:
                db.add(Obra(**o))
            await db.commit()

        if (await db.execute(select(Servicio))).scalars().first() is None:
            for s in SERVICIOS:
                db.add(Servicio(**s))
            await db.commit()

    entrenar_y_guardar(OBRAS)
    print("Seed completado: roles, usuarios de prueba, obras y servicios listos.")
    print("Credenciales de prueba:")
    for u in USUARIOS:
        print(f"  {u['rol']}: {u['email']} / {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
