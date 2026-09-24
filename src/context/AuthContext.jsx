import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../services/api";

const AuthContext = createContext(null);

const TOKEN_KEY = "oleo_lienzo_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  // Al montar (o si hay un token guardado), valida contra el backend con /auth/me.
  useEffect(() => {
    let activo = true;
    async function cargarUsuario() {
      if (!token) {
        setCargando(false);
        return;
      }
      try {
        const data = await api.me(token);
        if (activo) setUsuario(data);
      } catch {
        // token inválido o expirado
        if (activo) {
          setToken(null);
          localStorage.removeItem(TOKEN_KEY);
        }
      } finally {
        if (activo) setCargando(false);
      }
    }
    cargarUsuario();
    return () => {
      activo = false;
    };
  }, [token]);

  async function login(email, password) {
    const data = await api.login(email, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setToken(data.access_token);
    setUsuario(data.usuario);
    return data.usuario;
  }

  async function registrar(datos) {
    return api.registro(datos);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUsuario(null);
  }

  const value = {
    usuario,
    token,
    cargando,
    autenticado: Boolean(usuario),
    rol: usuario?.rol?.nombre ?? null,
    login,
    registrar,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
