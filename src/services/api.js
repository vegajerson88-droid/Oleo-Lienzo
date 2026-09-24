const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Extrae un mensaje legible del cuerpo de error uniforme del backend
 * ({ error, detail }) o de los errores de validación de Pydantic
 * (detail: [{ loc, msg }, ...]).
 */
function mensajeDesdeError(body) {
  if (!body) return "Ocurrió un error inesperado.";
  const { detail } = body;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (Array.isArray(d.loc) ? `${d.loc[d.loc.length - 1]}: ${d.msg}` : d.msg))
      .join(" ");
  }
  return "Ocurrió un error inesperado.";
}

async function request(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(
      "No se pudo conectar con el servidor. Verifica tu conexión.",
      0,
      null
    );
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    // respuesta sin cuerpo JSON
  }

  if (!response.ok) {
    throw new ApiError(mensajeDesdeError(data), response.status, data?.detail);
  }
  return data;
}

export const api = {
  registro: (datos) => request("/auth/registro", { method: "POST", body: datos }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: { email, password } }),
  me: (token) => request("/auth/me", { token }),

  listarObras: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/productos${qs ? `?${qs}` : ""}`);
  },
  crearObra: (datos, token) => request("/productos", { method: "POST", body: datos, token }),
  actualizarObra: (id, datos, token) =>
    request(`/productos/${id}`, { method: "PATCH", body: datos, token }),
  eliminarObra: (id, token) => request(`/productos/${id}`, { method: "DELETE", token }),

  listarServicios: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/servicios${qs ? `?${qs}` : ""}`);
  },
  crearServicio: (datos, token) => request("/servicios", { method: "POST", body: datos, token }),
  actualizarServicio: (id, datos, token) =>
    request(`/servicios/${id}`, { method: "PATCH", body: datos, token }),
  eliminarServicio: (id, token) => request(`/servicios/${id}`, { method: "DELETE", token }),

  crearPedido: (detalles, token) =>
    request("/pedidos", { method: "POST", body: { detalles }, token }),
  listarPedidos: (token, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/pedidos${qs ? `?${qs}` : ""}`, { token });
  },
  cambiarEstadoPedido: (pedidoId, nuevoEstado, token) =>
    request(`/pedidos/${pedidoId}/estado`, {
      method: "PATCH",
      body: { nuevo_estado: nuevoEstado },
      token,
    }),

  listarUsuarios: (token, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/usuarios${qs ? `?${qs}` : ""}`, { token });
  },
  actualizarUsuario: (id, datos, token) =>
    request(`/usuarios/${id}`, { method: "PATCH", body: datos, token }),
  eliminarUsuario: (id, token) => request(`/usuarios/${id}`, { method: "DELETE", token }),

  diagnostico: (token) => request("/sistema/diagnostico", { token }),
  precioSugerido: (anio, tecnica, token) => {
    const qs = new URLSearchParams({ anio, tecnica }).toString();
    return request(`/ia/precio-sugerido?${qs}`, { token });
  },
  descripcionSugerida: (titulo, tecnica, token) => {
    const qs = new URLSearchParams({ titulo, tecnica }).toString();
    return request(`/ia/descripcion-sugerida?${qs}`, { token });
  },
};

export { ApiError };
