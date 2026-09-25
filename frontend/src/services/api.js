/**
 * Cliente HTTP centralizado.
 *
 * Todas las llamadas al backend pasan por aquí: un único sitio donde se
 * resuelve la URL base, se adjunta el token, se normalizan los errores y se
 * gestionan las descargas de archivos.
 *
 * La URL del backend NO está escrita en el código: llega de la variable de
 * entorno VITE_API_URL (ver frontend/.env.example).
 */
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const BASE = `${API_URL}/api`;

/** Error de la API con el código HTTP y el detalle del backend. */
export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }

  get esNoAutenticado() {
    return this.status === 401;
  }

  get esSinPermiso() {
    return this.status === 403;
  }

  get esConflicto() {
    return this.status === 409;
  }

  get esValidacion() {
    return this.status === 422;
  }

  get esDeRed() {
    return this.status === 0;
  }
}

/**
 * Extrae un mensaje legible del cuerpo de error del backend, que puede venir
 * como string ({detail: "..."}) o como la lista de errores de Pydantic
 * ({detail: [{loc, msg}, ...]}).
 */
function mensajeDesdeError(cuerpo, status) {
  if (!cuerpo) return `Error ${status}: la solicitud no pudo completarse.`;

  const { detail } = cuerpo;
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const campo = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : null;
        return campo ? `${campo}: ${d.msg}` : d.msg;
      })
      .join(" · ");
  }

  return `Error ${status}: la solicitud no pudo completarse.`;
}

/** Convierte un objeto en query string, omitiendo valores vacíos. */
function queryString(params = {}) {
  const limpio = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );
  if (limpio.length === 0) return "";
  return `?${new URLSearchParams(limpio).toString()}`;
}

async function request(path, { method = "GET", body, token, signal } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError(
      "No se pudo conectar con el servidor. Comprueba que el backend esté en marcha.",
      0,
      null
    );
  }

  if (respuesta.status === 204) return null;

  let datos = null;
  try {
    datos = await respuesta.json();
  } catch {
    // respuesta sin cuerpo JSON
  }

  if (!respuesta.ok) {
    throw new ApiError(mensajeDesdeError(datos, respuesta.status), respuesta.status, datos?.detail);
  }
  return datos;
}

/** Descarga un archivo (PDF o Excel) y dispara el guardado en el navegador. */
async function descargar(path, { token, nombrePorDefecto }) {
  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor.", 0, null);
  }

  if (!respuesta.ok) {
    let datos = null;
    try {
      datos = await respuesta.json();
    } catch {
      /* el cuerpo del error no era JSON */
    }
    throw new ApiError(mensajeDesdeError(datos, respuesta.status), respuesta.status, null);
  }

  // El backend indica el nombre del archivo en Content-Disposition.
  const disposicion = respuesta.headers.get("Content-Disposition") || "";
  const coincidencia = disposicion.match(/filename="?([^";]+)"?/);
  const nombre = coincidencia ? coincidencia[1] : nombrePorDefecto;

  const blob = await respuesta.blob();
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
  return nombre;
}

export const api = {
  // ── Autenticación ────────────────────────────────────────────────────
  registro: (datos) => request("/auth/registro", { method: "POST", body: datos }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: { email, password } }),
  me: (token, signal) => request("/auth/me", { token, signal }),
  recuperarPassword: (email) =>
    request("/auth/recuperar-password", { method: "POST", body: { email } }),
  restablecerPassword: (token, password, confirmarPassword) =>
    request("/auth/restablecer-password", {
      method: "POST",
      body: { token, password, confirmar_password: confirmarPassword },
    }),
  cambiarPassword: (passwordActual, passwordNueva, token) =>
    request("/auth/cambiar-password", {
      method: "POST",
      body: { password_actual: passwordActual, password_nueva: passwordNueva },
      token,
    }),

  // ── Obras (productos) ────────────────────────────────────────────────
  listarObras: (params, signal) => request(`/productos${queryString(params)}`, { signal }),
  obtenerObra: (id) => request(`/productos/${id}`),
  crearObra: (datos, token) => request("/productos", { method: "POST", body: datos, token }),
  reemplazarObra: (id, datos, token) =>
    request(`/productos/${id}`, { method: "PUT", body: datos, token }),
  actualizarObra: (id, datos, token) =>
    request(`/productos/${id}`, { method: "PATCH", body: datos, token }),
  eliminarObra: (id, token) => request(`/productos/${id}`, { method: "DELETE", token }),

  // ── Servicios ────────────────────────────────────────────────────────
  listarServicios: (params, signal) => request(`/servicios${queryString(params)}`, { signal }),
  crearServicio: (datos, token) => request("/servicios", { method: "POST", body: datos, token }),
  reemplazarServicio: (id, datos, token) =>
    request(`/servicios/${id}`, { method: "PUT", body: datos, token }),
  actualizarServicio: (id, datos, token) =>
    request(`/servicios/${id}`, { method: "PATCH", body: datos, token }),
  eliminarServicio: (id, token) => request(`/servicios/${id}`, { method: "DELETE", token }),

  // ── Usuarios ─────────────────────────────────────────────────────────
  listarUsuarios: (token, params, signal) =>
    request(`/usuarios${queryString(params)}`, { token, signal }),
  listarRoles: (token) => request("/usuarios/roles", { token }),
  crearUsuario: (datos, token) => request("/usuarios", { method: "POST", body: datos, token }),
  reemplazarUsuario: (id, datos, token) =>
    request(`/usuarios/${id}`, { method: "PUT", body: datos, token }),
  actualizarUsuario: (id, datos, token) =>
    request(`/usuarios/${id}`, { method: "PATCH", body: datos, token }),
  cambiarEstadoUsuario: (id, activo, token) =>
    request(`/usuarios/${id}/estado`, { method: "PATCH", body: { activo }, token }),
  eliminarUsuario: (id, token) => request(`/usuarios/${id}`, { method: "DELETE", token }),

  // ── Pedidos ──────────────────────────────────────────────────────────
  crearPedido: (detalles, token) =>
    request("/pedidos", { method: "POST", body: { detalles }, token }),
  listarPedidos: (token, params, signal) =>
    request(`/pedidos${queryString(params)}`, { token, signal }),
  cambiarEstadoPedido: (id, nuevoEstado, token) =>
    request(`/pedidos/${id}/estado`, {
      method: "PATCH",
      body: { nuevo_estado: nuevoEstado },
      token,
    }),

  // ── Ventas ───────────────────────────────────────────────────────────
  listarVentas: (token, params, signal) =>
    request(`/ventas${queryString(params)}`, { token, signal }),
  obtenerVenta: (id, token) => request(`/ventas/${id}`, { token }),
  crearVenta: (datos, token) => request("/ventas", { method: "POST", body: datos, token }),
  cambiarEstadoVenta: (id, nuevoEstado, token) =>
    request(`/ventas/${id}/estado`, {
      method: "PATCH",
      body: { nuevo_estado: nuevoEstado },
      token,
    }),

  // ── Facturas ─────────────────────────────────────────────────────────
  listarFacturas: (token, params, signal) =>
    request(`/facturas${queryString(params)}`, { token, signal }),
  emitirFactura: (ventaId, observaciones, token) =>
    request("/facturas", {
      method: "POST",
      body: { venta_id: ventaId, observaciones: observaciones || null },
      token,
    }),
  cambiarEstadoFactura: (id, nuevoEstado, token) =>
    request(`/facturas/${id}/estado`, {
      method: "PATCH",
      body: { nuevo_estado: nuevoEstado },
      token,
    }),
  descargarFacturaPdf: (id, numero, token) =>
    descargar(`/facturas/${id}/pdf`, { token, nombrePorDefecto: `factura-${numero}.pdf` }),

  // ── Reportes ─────────────────────────────────────────────────────────
  reporteDiario: (token, dia, signal) =>
    request(`/reportes/ventas-diarias${queryString({ dia })}`, { token, signal }),
  descargarReportePdf: (dia, token) =>
    descargar(`/reportes/ventas-diarias/pdf${queryString({ dia })}`, {
      token,
      nombrePorDefecto: `reporte-ventas-${dia}.pdf`,
    }),
  descargarReporteExcel: (dia, token) =>
    descargar(`/reportes/ventas-diarias/excel${queryString({ dia })}`, {
      token,
      nombrePorDefecto: `reporte-ventas-${dia}.xlsx`,
    }),

  // ── Dashboard ────────────────────────────────────────────────────────
  dashboard: (token, params, signal) =>
    request(`/dashboard${queryString(params)}`, { token, signal }),

  // ── PQR ──────────────────────────────────────────────────────────────
  radicarPqr: (datos, token) => request("/pqr", { method: "POST", body: datos, token }),
  listarPqr: (token, params, signal) => request(`/pqr${queryString(params)}`, { token, signal }),
  responderPqr: (id, respuesta, token) =>
    request(`/pqr/${id}/responder`, { method: "POST", body: { respuesta }, token }),
  cambiarEstadoPqr: (id, nuevoEstado, token) =>
    request(`/pqr/${id}/estado`, { method: "PATCH", body: { nuevo_estado: nuevoEstado }, token }),

  // ── Chatbot ──────────────────────────────────────────────────────────
  enviarMensajeChat: (mensaje, sessionId, token) =>
    request("/chatbot/mensaje", {
      method: "POST",
      body: { mensaje, session_id: sessionId },
      token,
    }),

  // ── Pagos ────────────────────────────────────────────────────────────
  configuracionPagos: () => request("/pagos/configuracion"),
  crearCheckout: (ventaId, token) =>
    request("/pagos/checkout", { method: "POST", body: { venta_id: ventaId }, token }),

  // ── Sistema e IA ─────────────────────────────────────────────────────
  diagnostico: (token) => request("/sistema/diagnostico", { token }),
  precioSugerido: (anio, tecnica, token) =>
    request(`/ia/precio-sugerido${queryString({ anio, tecnica })}`, { token }),
  descripcionSugerida: (titulo, tecnica, token) =>
    request(`/ia/descripcion-sugerida${queryString({ titulo, tecnica })}`, { token }),
};
