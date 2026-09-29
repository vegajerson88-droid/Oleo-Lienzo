"""Captura las pantallas del proyecto para el Manual Técnico.

Recorre la aplicación como lo haría una persona —inicia sesión con cada rol y
entra en cada sección— y guarda una captura de cada pantalla en
`docs/manual/capturas/`.

Automatizarlo en vez de tomar las capturas a mano tiene dos ventajas: se
pueden regenerar todas cuando cambie la interfaz, y nunca falta ninguna.

Requisitos: el backend en :8000 y el frontend en :5173, y `python seed.py`
ejecutado para que haya datos que mostrar.

Uso:  python scripts/capturar_evidencias.py
"""

import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent.parent
DESTINO = RAIZ / "docs" / "manual" / "capturas"
FRONTEND = "http://localhost:5173"
BACKEND = "http://localhost:8000"

CREDENCIALES = {
    "administrador": ("admin@oleoylienzo.com", "Admin1234"),
    "empleado": ("empleado@oleoylienzo.com", "Empleado123"),
    "cliente": ("cliente@oleoylienzo.com", "Cliente123"),
}

# (archivo, descripción, ruta, rol o None si es pública, pestaña del panel)
PANTALLAS = [
    ("01-inicio", "Página de inicio con el carrusel", "/", None, None),
    ("02-catalogo", "Catálogo de obras", "/catalogo", None, None),
    ("03-quienes-somos", "Quiénes somos", "/quienes-somos", None, None),
    ("04-contacto", "Formulario de contacto", "/contacto", None, None),
    ("05-login", "Inicio de sesión", "/login", None, None),
    (
        "06-panel-admin-dashboard",
        "Dashboard del administrador",
        "/panel/administrador",
        "administrador",
        "dashboard",
    ),
    (
        "07-panel-admin-ventas",
        "Historial de ventas",
        "/panel/administrador",
        "administrador",
        "ventas",
    ),
    ("08-panel-admin-facturas", "Facturación", "/panel/administrador", "administrador", "facturas"),
    (
        "09-panel-admin-reportes",
        "Reporte diario de ventas",
        "/panel/administrador",
        "administrador",
        "reportes",
    ),
    (
        "10-panel-admin-obras",
        "Gestión del catálogo",
        "/panel/administrador",
        "administrador",
        "obras",
    ),
    (
        "11-panel-admin-usuarios",
        "Gestión de usuarios",
        "/panel/administrador",
        "administrador",
        "usuarios",
    ),
    ("12-panel-admin-pqr", "Gestión de PQR", "/panel/administrador", "administrador", "pqr"),
    ("13-panel-empleado", "Panel del empleado", "/panel/empleado", "empleado", "dashboard"),
    ("14-panel-cliente", "Panel del cliente", "/panel/cliente", "cliente", "resumen"),
    ("15-panel-cliente-pedidos", "Mis pedidos", "/panel/cliente", "cliente", "pedidos"),
]


def iniciar_sesion(page, rol: str) -> bool:
    email, password = CREDENCIALES[rol]
    page.goto(f"{FRONTEND}/login", wait_until="networkidle")
    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    try:
        page.wait_for_url(lambda url: "/login" not in url, timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        return True
    except PlaywrightTimeout:
        print(f"    no se pudo iniciar sesión como {rol}")
        return False


def cerrar_sesion(page) -> None:
    page.goto(FRONTEND, wait_until="domcontentloaded")
    page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")


def capturar(page, archivo: str, descripcion: str) -> None:
    ruta = DESTINO / f"{archivo}.png"
    page.screenshot(path=str(ruta), full_page=True)
    tam = ruta.stat().st_size // 1024
    print(f"  ✅ {archivo:32} {descripcion:38} {tam} KB")


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    rol_actual = None

    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
        contexto = navegador.new_context(viewport={"width": 1440, "height": 950})
        page = contexto.new_page()

        print(f"\nCapturando en {DESTINO}\n")

        for archivo, descripcion, ruta, rol, pestania in PANTALLAS:
            if rol != rol_actual:
                cerrar_sesion(page)
                rol_actual = None
                if rol and iniciar_sesion(page, rol):
                    rol_actual = rol
                elif rol:
                    continue

            page.goto(f"{FRONTEND}{ruta}", wait_until="networkidle")

            if pestania:
                # Las secciones del panel son pestañas dentro de la misma ruta.
                try:
                    page.get_by_role("tab", name=pestania, exact=False).first.click(timeout=4000)
                    page.wait_for_load_state("networkidle", timeout=8000)
                except PlaywrightTimeout:
                    pass

            page.wait_for_timeout(1200)  # deja asentar gráficos y animaciones
            capturar(page, archivo, descripcion)

        # La documentación automática de la API, como evidencia aparte.
        page.goto(f"{BACKEND}/docs", wait_until="networkidle")
        page.wait_for_timeout(2500)
        capturar(page, "16-swagger", "Documentación automática (Swagger)")

        navegador.close()

    total = len(list(DESTINO.glob("*.png")))
    print(f"\n{total} capturas en {DESTINO}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
