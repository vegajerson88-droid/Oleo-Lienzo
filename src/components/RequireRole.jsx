import { Navigate, useLocation } from "react-router-dom";
import { Loader2, ShieldAlert } from "lucide-react";

import { useAuth } from "../context/AuthContext";

/**
 * Protege una ruta: exige sesión y, si se indican, uno de los roles dados.
 *
 * Es una comodidad de la interfaz, no la medida de seguridad: quien autoriza
 * de verdad es el backend, que rechaza con 401 o 403 cualquier petición
 * indebida aunque alguien fuerce la URL en el navegador.
 */
function RequireRole({ roles, children }) {
  const { autenticado, rol, cargando, rutaPanel } = useAuth();
  const ubicacion = useLocation();

  if (cargando) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-muted">
        <Loader2 size={28} className="animate-spin text-gold" aria-hidden="true" />
        <p className="etiqueta">Comprobando tu sesión…</p>
      </div>
    );
  }

  // Sin sesión: al login, recordando a dónde quería ir.
  if (!autenticado) {
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />;
  }

  // Con sesión pero sin el rol necesario.
  if (roles && !roles.includes(rol)) {
    return (
      <div className="contenedor flex min-h-[60vh] flex-col items-center justify-center py-16 text-center">
        <span className="mb-5 flex h-16 w-16 items-center justify-center rounded-full
                         border border-error/30 bg-error-suave text-error">
          <ShieldAlert size={28} aria-hidden="true" />
        </span>
        <h1 className="font-display text-2xl">No tienes acceso a esta sección</h1>
        <p className="mt-2 max-w-md text-sm text-muted">
          Tu rol actual es <strong className="text-ink">{rol}</strong> y esta página
          está reservada a: {roles.join(", ")}.
        </p>
        <Navigate to={rutaPanel} replace />
      </div>
    );
  }

  return children;
}

export default RequireRole;
