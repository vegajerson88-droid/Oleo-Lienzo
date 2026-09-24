import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "../services/api";

const AuthContext = createContext(null);

const CLAVE_TOKEN = "oleo_lienzo_token";

/**
 * Lee el token guardado.
 *
 * Se mira primero `localStorage` (la sesión persiste al cerrar el navegador,
 * que es lo que pide "Recordarme") y después `sessionStorage` (la sesión
 * muere con la pestaña).
 */
function leerTokenGuardado() {
  try {
    return localStorage.getItem(CLAVE_TOKEN) || sessionStorage.getItem(CLAVE_TOKEN);
  } catch {
    // Modo privado con almacenamiento bloqueado: se sigue sin sesión previa.
    return null;
  }
}

function guardarToken(token, recordarme) {
  try {
    localStorage.removeItem(CLAVE_TOKEN);
    sessionStorage.removeItem(CLAVE_TOKEN);
    (recordarme ? localStorage : sessionStorage).setItem(CLAVE_TOKEN, token);
  } catch {
    // Sin almacenamiento la sesión vive solo en memoria; la aplicación sigue.
  }
}

function borrarToken() {
  try {
    localStorage.removeItem(CLAVE_TOKEN);
    sessionStorage.removeItem(CLAVE_TOKEN);
  } catch {
    /* nada que limpiar */
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(leerTokenGuardado);
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(Boolean(leerTokenGuardado()));

  // Valida el token contra el backend: quien decide si la sesión sirve es el
  // servidor, no lo que haya guardado el navegador.
  useEffect(() => {
    if (!token) {
      setUsuario(null);
      setCargando(false);
      return;
    }

    const controlador = new AbortController();
    let vigente = true;

    (async () => {
      setCargando(true);
      try {
        const datos = await api.me(token, controlador.signal);
        if (vigente) setUsuario(datos);
      } catch (error) {
        if (error.name === "AbortError") return;
        // Token caducado, revocado o usuario desactivado.
        if (vigente) {
          borrarToken();
          setToken(null);
          setUsuario(null);
        }
      } finally {
        if (vigente) setCargando(false);
      }
    })();

    return () => {
      vigente = false;
      controlador.abort();
    };
  }, [token]);

  const login = useCallback(async (email, password, recordarme = false) => {
    const datos = await api.login(email, password);
    guardarToken(datos.access_token, recordarme);
    setToken(datos.access_token);
    setUsuario(datos.usuario);
    return datos.usuario;
  }, []);

  const registrar = useCallback((datos) => api.registro(datos), []);

  const logout = useCallback(() => {
    borrarToken();
    setToken(null);
    setUsuario(null);
  }, []);

  const refrescarUsuario = useCallback(async () => {
    if (!token) return null;
    const datos = await api.me(token);
    setUsuario(datos);
    return datos;
  }, [token]);

  const valor = useMemo(() => {
    const rol = usuario?.rol?.nombre ?? null;
    const permisos = usuario?.rol?.permisos?.map((p) => p.codigo) ?? [];
    return {
      usuario,
      token,
      cargando,
      autenticado: Boolean(usuario),
      rol,
      permisos,
      esAdministrador: rol === "administrador",
      esEmpleado: rol === "empleado",
      esCliente: rol === "cliente",
      /** Comprobación fina de permisos (la definitiva la hace el backend). */
      tienePermiso: (codigo) => permisos.includes(codigo),
      /** Ruta del panel que corresponde al rol del usuario. */
      rutaPanel:
        rol === "administrador" ? "/panel/administrador"
        : rol === "empleado" ? "/panel/empleado"
        : rol === "cliente" ? "/panel/cliente"
        : "/login",
      login,
      registrar,
      logout,
      refrescarUsuario,
    };
  }, [usuario, token, cargando, login, registrar, logout, refrescarUsuario]);

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const contexto = useContext(AuthContext);
  if (!contexto) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return contexto;
}
