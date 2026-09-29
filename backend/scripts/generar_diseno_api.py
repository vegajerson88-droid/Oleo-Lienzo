"""Genera docs/diseno-api.md: la tabla recurso–verbo–ruta–código.

Se genera a partir del esquema OpenAPI real en vez de escribirse a mano, de
modo que la tabla de diseño y la API implementada nunca puedan divergir.

Uso:  python scripts/generar_diseno_api.py
"""

import sys
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_BACKEND))

from app.main import app  # noqa: E402

DESTINO = RAIZ_BACKEND.parent / "docs" / "diseno-api.md"

# Orden de presentación de los recursos, del núcleo del dominio hacia fuera.
ORDEN = [
    "Autenticación",
    "Usuarios",
    "Obras / Productos",
    "Servicios",
    "Pedidos",
    "Ventas",
    "Facturación",
    "Reportes",
    "Dashboard",
    "PQR",
    "Chatbot IA",
    "Inteligencia Artificial",
    "Pagos (Stripe)",
    "Sistema",
]

# Quién puede llamar a cada recurso. La autorización real la imponen las
# dependencias del router; esta columna solo la documenta.
AUTORIZACION = {
    "Autenticación": "Pública (salvo `/me` y cambio de contraseña)",
    "Usuarios": "Administrador",
    "Obras / Productos": "Lectura pública · escritura administrador o empleado",
    "Servicios": "Lectura pública · escritura administrador o empleado",
    "Pedidos": "Cliente (los suyos) · administrador y empleado (todos)",
    "Ventas": "Administrador y empleado · el cliente ve las suyas",
    "Facturación": "Administrador y empleado · el cliente ve las suyas",
    "Reportes": "Administrador y empleado",
    "Dashboard": "Autenticado, con el contenido recortado según el rol",
    "PQR": "Cliente radica · administrador y empleado gestionan",
    "Chatbot IA": "Pública",
    "Inteligencia Artificial": "Administrador y empleado",
    "Pagos (Stripe)": "Cliente · el webhook lo llama Stripe con firma",
    "Sistema": "`/salud` pública · `/diagnostico` administrador",
}

CABECERA = """# Diseño de la API — recurso, verbo, ruta y código

Tabla de diseño de la API REST de Óleo & Lienzo: para cada recurso, qué verbo
HTTP le corresponde a cada operación, en qué ruta vive y con qué código
responde.

## Criterios de diseño aplicados

1. **Las rutas nombran recursos, no acciones.** `/api/productos`, no
   `/api/obtenerProductos`. El verbo HTTP dice qué se hace; la ruta, sobre qué.
2. **Los recursos van en plural.** `/api/ventas/{id}`, no `/api/venta/{id}`.
3. **Cada verbo tiene un significado fijo.** `GET` consulta, `POST` crea,
   `PUT` reemplaza por completo, `PATCH` modifica parcialmente y `DELETE`
   elimina.
4. **Las operaciones de negocio que no son un CRUD se modelan como
   sub-recurso**, no como un `PATCH` genérico: `POST /api/pqr/{id}/responder`
   expresa la intención mucho mejor que mandar un campo suelto.
5. **El cliente no decide los campos del servidor.** Ni el identificador, ni
   los consecutivos (`V-2026-000001`, `OL-000001`, `PQR-000001`), ni las
   fechas, ni el estado: los esquemas de entrada ni siquiera los aceptan.
6. **Los códigos son los del protocolo.** `201` al crear devolviendo el
   recurso, `204` al eliminar sin cuerpo, `409` para un conflicto de negocio
   (nunca `400` ni `500`), `422` para validación.

## Excepción consciente: las rutas de autenticación

`/api/auth/login`, `/api/auth/registro` y las de contraseña llevan un verbo en
la ruta. Es la convención establecida para autenticación —la usan OAuth2 y
prácticamente todas las APIs— y se ha preferido a forzar un sustantivo
artificial como `/api/sesiones`, que sería más purista pero menos reconocible.

## Formato uniforme de error

Todos los errores, los lance quien los lance, salen con el mismo cuerpo:

```json
{ "error": "NotFound", "detail": "Obra 42 no encontrada." }
```

En un `422` de validación, `detail` es la lista de campos que fallaron.

---

"""

PIE = """
---

## Códigos de respuesta y cuándo se usan

| Código | Cuándo |
|---|---|
| `200 OK` | Consulta o modificación correcta |
| `201 Created` | Recurso creado; el cuerpo lleva el recurso con su id |
| `204 No Content` | Eliminación correcta, sin cuerpo |
| `401 Unauthorized` | Falta el token o no es válido. Incluye `WWW-Authenticate: Bearer` |
| `403 Forbidden` | Autenticado, pero su rol no alcanza |
| `404 Not Found` | El recurso no existe |
| `409 Conflict` | Duplicado o restricción única: correo ya registrado, venta ya facturada |
| `422 Unprocessable Content` | Validación fallida o regla de negocio incumplida |
| `429 Too Many Requests` | Se superó el límite de intentos |
| `500 Internal Server Error` | Error inesperado. La traza va al log, nunca al cliente |

---

*Generado desde el esquema OpenAPI con `scripts/generar_diseno_api.py`.
No editar a mano: la tabla y la API implementada se mantienen así en sintonía.*
"""


def codigos_de(operacion: dict) -> str:
    """Códigos declarados en la operación, los correctos primero."""
    codigos = sorted(c for c in operacion.get("responses", {}) if c.isdigit())
    # El 422 que FastAPI añade solo aparece si la operación valida algo.
    return " · ".join(f"`{c}`" for c in codigos)


def main() -> None:
    esquema = app.openapi()
    por_etiqueta: dict[str, list[tuple[str, str, dict]]] = {}

    for ruta, metodos in esquema["paths"].items():
        for verbo, operacion in metodos.items():
            etiqueta = (operacion.get("tags") or ["Sistema"])[0]
            por_etiqueta.setdefault(etiqueta, []).append((verbo.upper(), ruta, operacion))

    partes = [CABECERA]
    total = 0

    etiquetas = ORDEN + [e for e in por_etiqueta if e not in ORDEN]
    for etiqueta in etiquetas:
        operaciones = por_etiqueta.get(etiqueta)
        if not operaciones:
            continue
        partes.append(f"## {etiqueta}\n")
        if etiqueta in AUTORIZACION:
            partes.append(f"**Quién puede:** {AUTORIZACION[etiqueta]}\n")
        partes.append("| Verbo | Ruta | Operación | Códigos |")
        partes.append("|---|---|---|---|")
        # Primero los listados y las altas, después lo que opera sobre un id.
        for verbo, ruta, operacion in sorted(operaciones, key=lambda o: ("{" in o[1], o[1], o[0])):
            resumen = operacion.get("summary", "").rstrip(".")
            partes.append(f"| `{verbo}` | `{ruta}` | {resumen} | {codigos_de(operacion)} |")
            total += 1
        partes.append("")

    partes.append(f"**Total: {total} operaciones** repartidas en {len(por_etiqueta)} recursos.")
    partes.append(PIE)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text("\n".join(partes), encoding="utf8")
    print(f"Generado {DESTINO}")
    print(f"  {total} operaciones · {len(por_etiqueta)} recursos")


if __name__ == "__main__":
    main()
