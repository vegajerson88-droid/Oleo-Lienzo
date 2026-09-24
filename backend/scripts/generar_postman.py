"""Genera la colección de Postman a partir del esquema OpenAPI de la API.

Generarla en vez de escribirla a mano evita que la colección se quede
desfasada cuando cambia un endpoint.

Uso:  python scripts/generar_postman.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

DESTINO = Path(__file__).resolve().parent.parent.parent / "postman" / "Oleo-Lienzo.postman_collection.json"

# Endpoints que no necesitan token.
PUBLICOS = {
    ("post", "/api/auth/registro"), ("post", "/api/auth/login"),
    ("post", "/api/auth/token"), ("post", "/api/auth/recuperar-password"),
    ("post", "/api/auth/restablecer-password"),
    ("get", "/api/productos"), ("get", "/api/productos/{obra_id}"),
    ("get", "/api/servicios"), ("get", "/api/servicios/{servicio_id}"),
    ("post", "/api/chatbot/mensaje"), ("post", "/api/pqr"),
    ("get", "/api/pagos/configuracion"), ("get", "/api/sistema/salud"),
    ("post", "/api/pagos/webhook"), ("get", "/"),
}

# Valores de ejemplo para los parámetros de ruta.
EJEMPLOS_RUTA = {
    "usuario_id": "1", "obra_id": "1", "servicio_id": "1", "pedido_id": "1",
    "venta_id": "1", "factura_id": "1", "pqr_id": "1", "conversacion_id": "1",
}


def resolver_ref(esquema: dict, componentes: dict) -> dict:
    """Sigue un $ref hasta el esquema real."""
    if "$ref" in esquema:
        nombre = esquema["$ref"].split("/")[-1]
        return componentes.get(nombre, {})
    return esquema


def cuerpo_de_ejemplo(operacion: dict, componentes: dict) -> str | None:
    cuerpo = operacion.get("requestBody", {})
    contenido = cuerpo.get("content", {}).get("application/json", {})
    if not contenido:
        return None

    esquema = resolver_ref(contenido.get("schema", {}), componentes)
    ejemplo = esquema.get("example") or (esquema.get("json_schema_extra") or {}).get("example")
    if ejemplo:
        return json.dumps(ejemplo, indent=2, ensure_ascii=False)

    # Sin ejemplo declarado: se construye uno a partir de las propiedades.
    propiedades = esquema.get("properties", {})
    if not propiedades:
        return "{}"

    def valor_por_defecto(prop: dict):
        prop = resolver_ref(prop, componentes)
        if "example" in prop:
            return prop["example"]
        if "default" in prop:
            return prop["default"]
        if prop.get("enum"):
            return prop["enum"][0]
        tipo = prop.get("type")
        if tipo == "integer":
            return 1
        if tipo == "number":
            return 1000
        if tipo == "boolean":
            return True
        if tipo == "array":
            return []
        return ""

    return json.dumps(
        {nombre: valor_por_defecto(prop) for nombre, prop in propiedades.items()},
        indent=2,
        ensure_ascii=False,
    )


def construir() -> dict:
    esquema = app.openapi()
    componentes = esquema.get("components", {}).get("schemas", {})

    carpetas: dict[str, list] = {}

    for ruta, metodos in esquema["paths"].items():
        for metodo, operacion in metodos.items():
            etiqueta = (operacion.get("tags") or ["General"])[0]
            requiere_token = (metodo, ruta) not in PUBLICOS

            # Sustituye {id} por :id y añade los valores de ejemplo.
            ruta_postman = ruta
            variables = []
            for parametro, valor in EJEMPLOS_RUTA.items():
                if f"{{{parametro}}}" in ruta_postman:
                    ruta_postman = ruta_postman.replace(f"{{{parametro}}}", f":{parametro}")
                    variables.append({"key": parametro, "value": valor})

            segmentos = [s for s in ruta_postman.strip("/").split("/") if s]

            consulta = [
                {
                    "key": p["name"],
                    "value": str(p.get("schema", {}).get("default", "")),
                    "description": p.get("description", ""),
                    "disabled": not p.get("required", False),
                }
                for p in operacion.get("parameters", [])
                if p.get("in") == "query"
            ]

            peticion = {
                "method": metodo.upper(),
                "header": [],
                "url": {
                    "raw": "{{base_url}}" + ruta_postman,
                    "host": ["{{base_url}}"],
                    "path": segmentos,
                },
                "description": (operacion.get("description") or operacion.get("summary") or ""),
            }
            if consulta:
                peticion["url"]["query"] = consulta
            if variables:
                peticion["url"]["variable"] = variables

            cuerpo = cuerpo_de_ejemplo(operacion, componentes)
            if cuerpo is not None:
                peticion["header"].append({"key": "Content-Type", "value": "application/json"})
                peticion["body"] = {"mode": "raw", "raw": cuerpo,
                                    "options": {"raw": {"language": "json"}}}

            if requiere_token:
                peticion["auth"] = {
                    "type": "bearer",
                    "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}],
                }
            else:
                peticion["auth"] = {"type": "noauth"}

            item = {
                "name": f"{metodo.upper()} {operacion.get('summary', ruta)}",
                "request": peticion,
                "response": [],
            }

            # El login guarda el token en la variable de la colección, para
            # que el resto de peticiones queden autenticadas sin copiar y pegar.
            if ruta == "/api/auth/login" and metodo == "post":
                item["event"] = [
                    {
                        "listen": "test",
                        "script": {
                            "type": "text/javascript",
                            "exec": [
                                "// Guarda el token para el resto de la colección.",
                                "if (pm.response.code === 200) {",
                                "  const datos = pm.response.json();",
                                "  pm.collectionVariables.set('token', datos.access_token);",
                                "  console.log('Token guardado para', datos.usuario.email);",
                                "}",
                                "pm.test('Devuelve 200 y un JWT', function () {",
                                "  pm.response.to.have.status(200);",
                                "  pm.expect(pm.response.json()).to.have.property('access_token');",
                                "});",
                            ],
                        },
                    }
                ]

            carpetas.setdefault(etiqueta, []).append(item)

    return {
        "info": {
            "name": "Óleo & Lienzo — API (React + Vite + FastAPI)",
            "description": (
                "Colección de pruebas de la API de Óleo & Lienzo.\n\n"
                "## Cómo usarla\n\n"
                "1. Arranca el backend: `uvicorn app.main:app --reload`.\n"
                "2. Ajusta la variable `base_url` si no usas el puerto 8000.\n"
                "3. Ejecuta **POST /api/auth/login** con las credenciales de "
                "prueba. El token se guarda solo en la variable `token` y el "
                "resto de peticiones lo usan automáticamente.\n\n"
                "## Credenciales de prueba (las crea `python seed.py`)\n\n"
                "| Rol | Correo | Contraseña |\n"
                "|---|---|---|\n"
                "| Administrador | admin@oleoylienzo.com | Admin1234 |\n"
                "| Empleado | empleado@oleoylienzo.com | Empleado123 |\n"
                "| Cliente | cliente@oleoylienzo.com | Cliente123 |\n\n"
                "## Para evidenciar el control de roles\n\n"
                "Inicia sesión como **cliente** y lanza `GET /api/usuarios`: "
                "debe responder **403**. Sin token, **401**."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000", "type": "string"},
            {"key": "token", "value": "", "type": "string"},
        ],
        "item": [
            {"name": etiqueta, "item": peticiones}
            for etiqueta, peticiones in sorted(carpetas.items())
        ],
    }


if __name__ == "__main__":
    coleccion = construir()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(coleccion, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(len(c["item"]) for c in coleccion["item"])
    print(f"Generada {DESTINO}")
    print(f"  {len(coleccion['item'])} carpetas · {total} peticiones")
