# Matriz final de cumplimiento

Verificación requisito por requisito de los cuatro entregables y de la Matriz
de Validación Técnica del SENA.

**Estados:** ✅ Completo · ⚠️ Parcial · ❌ Pendiente

**Fecha de la auditoría:** 24 de septiembre de 2026
**Verificado con:** 141 pruebas automatizadas (SQLite y PostgreSQL), pruebas
manuales por API y recorrido completo en navegador real.

---

## Resumen

| Entregable | Requisitos | ✅ | ⚠️ | ❌ |
|---|---:|---:|---:|---:|
| Segundo avance — React + Tailwind | 21 | 21 | 0 | 0 |
| Tercer avance — Backend, BD, JWT, roles | 25 | 25 | 0 | 0 |
| Cuarto avance — FastAPI | 31 | 31 | 0 | 0 |
| Quinto avance — Gestión comercial e IA | 20 | 19 | 1 | 0 |
| Matriz de validación SENA | 24 | 24 | 0 | 0 |
| **Total** | **121** | **120** | **1** | **0** |

El único punto no cerrado es el **despliegue con URL pública**, que necesita
las credenciales de la plataforma de quien presenta el proyecto. Todo lo
necesario está preparado (`Dockerfile`, `railway.json`, `docker-compose.yml`
y la guía en `docs/despliegue.md`).

### Nota sobre el tercer avance

El tercer avance pedía un backend en **Node.js + Express**. El cuarto avance
indica expresamente *«reemplazando la tecnología del Backend por FastAPI»*, de
modo que el documento posterior sustituye a ese requisito. Los **requisitos
funcionales** del tercer avance (base de datos relacional, hashing, JWT,
roles, CRUD, paneles y endpoints) sí están todos cumplidos, implementados
sobre FastAPI.

---

## Segundo avance — React + Vite + Tailwind CSS

| # | Requisito | Estado | Evidencia |
|---|---|:---:|---|
| 1 | Tailwind CSS instalado y configurado con Vite | ✅ | `package.json` (`@tailwindcss/vite` v4), `vite.config.js` |
| 2 | Estilos aplicados con clases de Tailwind | ✅ | Toda la carpeta `src/` |
| 3 | Componentes existentes mejorados visualmente | ✅ | `src/components/` |
| 4 | Estilos en Header, Footer y Carousel | ✅ | `Header.jsx`, `Footer.jsx`, `Carousel.jsx` |
| 5 | Estilos en las páginas internas | ✅ | `src/pages/` |
| 6 | Interfaz responsiva | ✅ | Verificado a 375, 768 y 1440 px |
| 7 | Carrusel de 10 imágenes conservado | ✅ | `src/data/artData.js`, 10 obras |
| 8 | Cada imagen con título y descripción | ✅ | `Carousel.jsx` |
| 9 | Presentación del carrusel mejorada | ✅ | Pausa, teclado, indicadores, ficha técnica |
| 10 | Organización por componentes reutilizables | ✅ | `src/components/ui/` |
| 11 | Login con correo, contraseña, «Recordarme», botón, «¿Olvidaste tu contraseña?» y «Crear cuenta» | ✅ | `pages/Login.jsx` |
| 12 | Validaciones en tiempo real en el login | ✅ | `utils/validators.js` |
| 13 | `RecoverPassword` reutilizable e independiente | ✅ | `components/RecoverPassword.jsx` |
| 14 | Registro con los 9 campos exigidos | ✅ | `components/RegisterModal.jsx` |
| 15 | Registro dentro de un Modal | ✅ | `components/ui/Modal.jsx` |
| 16 | El Modal se cierra sin completar el registro | ✅ | Escape, clic fuera y botón Cancelar |
| 17 | Validaciones: obligatorios, longitudes, tipos, RegEx, correo, documento, teléfono, contraseña, confirmación y caracteres permitidos | ✅ | `utils/validators.js` |
| 18 | Componentes Login, RegisterModal, Input, Select, Button, Header, Footer, Carousel | ✅ | Los ocho existen, más 9 componentes nuevos |
| 19 | Uso de `useState` y `useEffect` | ✅ | En toda la aplicación, más hooks propios |
| 20 | React Router DOM con Index, Quiénes Somos y Contacto | ✅ | `App.jsx` |
| 21 | Imágenes en `src/assets/images` | ✅ | 10 archivos SVG |

---

## Tercer avance — Backend, base de datos, JWT y roles

| # | Requisito | Estado | Evidencia |
|---|---|:---:|---|
| 1 | Base de datos relacional SQL | ✅ | PostgreSQL 16, 15 tablas |
| 2 | Entidades usuarios, roles, permisos, productos y servicios | ✅ | `app/models/` |
| 3 | Tabla usuarios con los campos del formulario | ✅ | `models/usuario.py` |
| 4 | Contraseña almacenada con hashing | ✅ | bcrypt, `$2b$12$`, 60 caracteres |
| 5 | Campos de identificación, estado y rol | ✅ | `id`, `activo`, `rol_id` |
| 6 | Roles administrador, empleado y cliente | ✅ | `seed.py`, tabla `roles` |
| 7 | Carpeta backend independiente | ✅ | `backend/` |
| 8 | Dependencias: servidor, HTTP, BD, hashing, JWT, variables de entorno y CORS | ✅ | `requirements.txt` |
| 9 | Conexión Frontend → Backend → Base de datos | ✅ | Verificado extremo a extremo |
| 10 | El formulario de registro envía datos al backend | ✅ | `POST /api/auth/registro` |
| 11 | Inicio de sesión con generación de JWT | ✅ | `POST /api/auth/login` |
| 12 | Endpoints de usuarios, productos y servicios | ✅ | 19 operaciones sobre esas entidades |
| 13 | Endpoints protegidos mediante JWT | ✅ | `dependencies/auth.py` |
| 14 | Control de acceso según el rol | ✅ | `require_roles`, `require_permiso` |
| 15 | Operaciones CRUD completas | ✅ | `app/crud/` |
| 16 | Panel de administrador | ✅ | 10 secciones |
| 17 | Panel de empleado con privilegios reducidos | ✅ | 8 secciones, sin usuarios |
| 18 | Panel de cliente | ✅ | 4 secciones |
| 19 | Usuario autenticado visible en el Navbar | ✅ | «Hola, Ana» y botón Salir |
| 20 | Validaciones en frontend y backend | ✅ | `validators.js` y esquemas Pydantic |
| 21 | Componente flotante de WhatsApp | ✅ | `components/WhatsAppButton.jsx` |
| 22 | Estructura organizada del proyecto | ✅ | Ver README |
| 23 | Hashing seguro obligatorio | ✅ | bcrypt con sal por contraseña |
| 24 | Pruebas con Postman | ✅ | `postman/`, 60 peticiones |
| 25 | Script SQL de creación de la base de datos | ✅ | `backend/sql/schema_postgresql.sql` |

---

## Cuarto avance — FastAPI

| # | Requisito | Estado | Evidencia |
|---|---|:---:|---|
| 1 | Se conserva lo desarrollado antes | ✅ | Carrusel, formularios, validaciones, WhatsApp |
| 2 | Arquitectura React + Vite → FastAPI → SQL | ✅ | Ver README |
| 3 | Backend desarrollado con FastAPI | ✅ | `backend/app/` |
| 4 | Entorno virtual de Python | ✅ | Documentado en el README |
| 5 | Archivo `requirements.txt` | ✅ | `backend/requirements.txt` |
| 6 | Entidades usuarios, roles, permisos, productos y servicios | ✅ | Más ventas, facturas, pagos, PQR y chat |
| 7 | Tabla usuarios con rol y estado | ✅ | `models/usuario.py` |
| 8 | Contraseñas solo como hash | ✅ | Verificado en la base |
| 9 | Modelos y esquemas diferenciados | ✅ | `models/` frente a `schemas/` |
| 10 | Los esquemas validan tipos, obligatorios, longitudes y formatos | ✅ | `schemas/` con `Field` y validadores |
| 11 | Conexión configurada por variables de entorno | ✅ | `core/config.py` |
| 12 | `.env` fuera del repositorio | ✅ | `.gitignore`; solo se versionan los `.env.example` |
| 13 | Registro conectado a FastAPI | ✅ | Verificado |
| 14 | Se verifica que correo y documento no estén duplicados | ✅ | Responde 409 |
| 15 | Inicio de sesión conectado a FastAPI | ✅ | Verificado |
| 16 | JWT: existencia, validez, firma, expiración, usuario y rol | ✅ | `core/security.py`, con prueba de token caducado |
| 17 | Control de roles | ✅ | Pruebas de 403 por rol |
| 18 | Endpoints protegidos mediante dependencias | ✅ | `Depends(require_roles(...))` |
| 19 | Endpoints de usuarios, productos y servicios | ✅ | Los 17 del documento, más los nuevos |
| 20 | Métodos GET, POST, PUT, PATCH y DELETE | ✅ | Los cinco, con PUT y PATCH diferenciados |
| 21 | CRUD con estado activo/inactivo | ✅ | `PATCH /api/usuarios/{id}/estado` |
| 22 | Panel de administrador | ✅ | Verificado |
| 23 | Panel de empleado | ✅ | Verificado |
| 24 | Panel de cliente | ✅ | Verificado |
| 25 | Usuario autenticado en el Navbar | ✅ | Verificado |
| 26 | Validaciones en tiempo real conservadas y reforzadas | ✅ | Verificado |
| 27 | Seguridad de las contraseñas | ✅ | bcrypt |
| 28 | Información sensible en variables de entorno | ✅ | Sin secretos en el código |
| 29 | Componente de WhatsApp conservado | ✅ | Funciona sin backend |
| 30 | Documentación automática con Swagger | ✅ | `/docs` y `/redoc`, 60 operaciones |
| 31 | Pruebas con Postman | ✅ | Colección verificada contra la API |

---

## Quinto avance — Gestión comercial, analítica e IA

| # | Requisito | Estado | Evidencia |
|---|---|:---:|---|
| 1 | Módulo de ventas | ✅ | `models/venta.py`, `crud/venta.py` |
| 2 | Registro de productos y servicios vendidos | ✅ | `detalle_ventas`, con obra o servicio por línea |
| 3 | Historial de ventas con filtros | ✅ | Fecha, cliente, producto, servicio, estado y valor |
| 4 | Reporte diario de ventas | ✅ | `GET /api/reportes/ventas-diarias` |
| 5 | Exportación del reporte en PDF | ✅ | ReportLab, horizontal, con resumen y totales |
| 6 | Exportación del reporte en Excel | ✅ | openpyxl, con fórmulas, autofiltro y 2 hojas |
| 7 | Generación de facturas de venta | ✅ | Consecutivo `OL-NNNNNN` |
| 8 | Consulta de facturas | ✅ | Por número, cliente, estado y fecha |
| 9 | Descarga de la factura en PDF | ✅ | `GET /api/facturas/{id}/pdf` |
| 10 | Dashboard administrativo con tarjetas | ✅ | 12 indicadores |
| 11 | Dashboard de ventas con barras, líneas y tarjetas | ✅ | 4 gráficos |
| 12 | Dashboards según el rol | ✅ | 12 / 6 / 5 indicadores por rol |
| 13 | Filtros en los dashboards | ✅ | Rango de fechas |
| 14 | Nuevos endpoints en FastAPI | ✅ | De 27 a 60 operaciones |
| 15 | Los dashboards consumen la API, sin datos escritos a mano | ✅ | `crud/estadisticas.py`, con GROUP BY |
| 16 | Módulo de PQR | ✅ | Con radicado y 4 estados |
| 17 | Chatbot de atención al cliente | ✅ | Widget flotante |
| 18 | Chatbot integrado con Inteligencia Artificial | ✅ | Groq, con respaldo local declarado |
| 19 | Gestión segura de la API Key | ✅ | `GROQ_API_KEY` en `.env`, nunca en el código |
| 20 | **Despliegue con URL pública** | ⚠️ | Preparado: `Dockerfile`, `railway.json`, `docker-compose.yml` y `docs/despliegue.md`. **Falta ejecutar el despliegue con las credenciales del aprendiz.** |

### Requerimientos técnicos adicionales

| Requisito | Estado | Evidencia |
|---|:---:|---|
| Tablas ventas, detalle_ventas, facturas, pqr, conversaciones y mensajes | ✅ | Más `pagos`, `permisos` y `rol_permisos` |
| Endpoints, modelos y esquemas para lo nuevo | ✅ | Separación mantenida |
| Componentes reutilizables en React | ✅ | 13 componentes de interfaz y 3 de gráficos |
| Seguridad: JWT, roles, protección, hashing y variables de entorno | ✅ | Más limitación de intentos y cabeceras defensivas |
| Pruebas con Postman | ✅ | 60 peticiones |

---

## Matriz de Validación Técnica del SENA

| # | Criterio verificable | Estado | Evidencia |
|---|---|:---:|---|
| **1. Diseño y fundamentos REST** ||||
| 1.1 | Endpoints definidos con criterio REST | ✅ | Recurso, verbo, ruta y código coherentes |
| 1.2 | Parámetros de ruta y consulta validados (`Query`, `Path`, `Annotated`) | ✅ | `dependencies/common.py`: `IdPath = Annotated[int, Path(ge=1)]` |
| 1.3 | CRUD completo sobre los recursos principales | ✅ | Obras, servicios y usuarios |
| **2. Modelado y validación (Pydantic)** ||||
| 2.1 | Esquemas Pydantic v2 separados (Create / Update / Response) | ✅ | `ObraCreate`, `ObraReplace`, `ObraUpdate`, `ObraOut` |
| 2.2 | Validaciones propias del dominio | ✅ | `field_validator`, `model_validator` y restricciones de `Field` |
| **3. Persistencia (SQLAlchemy)** ||||
| 3.1 | Al menos dos entidades relacionadas con SQLAlchemy 2.0 | ✅ | 15 tablas, 20 claves foráneas |
| 3.2 | CRUD persistente contra una base real, no en memoria | ✅ | PostgreSQL 16 |
| **4. Autenticación y autorización** ||||
| 4.1 | Inicio de sesión con JWT (flujo OAuth2 password) | ✅ | `/api/auth/token` con `OAuth2PasswordRequestForm` |
| 4.2 | Endpoints protegidos según autenticación y rol | ✅ | Pruebas de 401 y 403 |
| **5. Errores y middlewares** ||||
| 5.1 | Errores estandarizados con códigos y mensajes claros | ✅ | Formato uniforme para 401, 403, 404, 409, 422 y 429 |
| 5.2 | CORS configurado para el frontend React | ✅ | `CORSMiddleware` con orígenes por variable de entorno |
| **6. Asincronía y tareas en segundo plano** ||||
| 6.1 | Al menos un flujo con `async/await` | ✅ | Toda la aplicación es asíncrona |
| 6.2 | `BackgroundTasks` para una tarea no bloqueante | ✅ | Seis correos distintos, en registro, pedidos, ventas y PQR |
| **7. Inteligencia Artificial** ||||
| 7.1 | Un endpoint que integre un modelo propio o un servicio externo | ✅ | Ambos: modelo de precios con scikit-learn y chatbot con Groq |
| 7.2 | Credenciales gestionadas por variables de entorno | ✅ | Verificado: los valores por defecto están vacíos |
| **8. Documentación y despliegue** ||||
| 8.1 | `/docs` y `/redoc` personalizadas con tags, descripciones y ejemplos | ✅ | 14 secciones, 60 operaciones documentadas |
| 8.2 | README con instrucciones, `requirements.txt` y `.env.example` | ✅ | `README.md` de 476 líneas |
| **9. Pruebas** ||||
| 9.1 | Pruebas con Pytest que cubren CRUD y autenticación | ✅ | 141 pruebas, verdes en SQLite y PostgreSQL |
| **10. Frontend React** ||||
| 10.1 | Cliente HTTP centralizado con la URL por variable de entorno | ✅ | `frontend/src/services/api.js`, `VITE_API_URL` |
| 10.2 | CRUD completamente funcional desde la interfaz | ✅ | Paneles de obras, servicios y usuarios |
| 10.3 | Formularios que reflejan los esquemas y validan en cliente | ✅ | `validators.js` como complemento, no sustituto |
| 10.4 | Estados de carga y de error bien gestionados | ✅ | `useRecurso`, Skeleton, Alert, Toast y EmptyState |
| **11. Comparativa y sustentación** ||||
| 11.1 | Análisis comparativo entre FastAPI y Django REST Framework | ✅ | `docs/comparativa-fastapi-drf.md` |
| 11.2 | Sustentación clara del funcionamiento y las decisiones | ✅ | `docs/evidencias.md` como guion de apoyo |

**Resultado: 24 de 24 criterios cumplidos.**

---

## Lo que queda pendiente

### Despliegue con URL pública

Es el único requisito sin cerrar, y no puede cerrarse sin las credenciales de
la plataforma.

**Ya está preparado:**

- `backend/Dockerfile` — imagen lista, sin ejecutar como root y con
  comprobación de salud.
- `railway.json` — configuración de construcción y arranque.
- `docker-compose.yml` — PostgreSQL y backend en local con un comando.
- `docs/despliegue.md` — guía paso a paso, con los errores frecuentes.
- `GET /api/sistema/salud` — endpoint público para el *health check*.

**Lo que falta hacer:**

1. Crear la cuenta en Railway y el servicio de PostgreSQL.
2. Desplegar el backend y rellenar sus variables de entorno.
3. Desplegar el frontend con `VITE_API_URL` apuntando al backend.
4. Añadir la URL del frontend a `CORS_ORIGINS`.

Tiempo estimado: entre 20 y 30 minutos siguiendo la guía.

---

## Cómo se verificó esta matriz

| Método | Alcance |
|---|---|
| **Pruebas automatizadas** | 141 pruebas con pytest, ejecutadas en SQLite y en PostgreSQL |
| **Pruebas por API** | Los 60 endpoints, con curl y con la colección de Postman |
| **Pruebas de navegador** | Recorrido completo con Playwright y Chromium: registro, inicio de sesión por rol, pedido, confirmación, venta, factura, descarga de PDF y de Excel |
| **Inspección de la base** | Consultas directas sobre PostgreSQL para comprobar tablas, restricciones y hashes |
| **Verificación del SQL** | El script se ejecutó en una base vacía y produjo un esquema idéntico al del ORM |

Nada de lo marcado como ✅ se dio por bueno solo porque exista el archivo: en
todos los casos se comprobó el comportamiento.
