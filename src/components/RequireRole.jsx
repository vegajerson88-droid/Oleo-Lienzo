import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/** Protege una ruta: exige sesión y, opcionalmente, uno de los roles dados. */
function RequireRole({ roles, children }) {
  const { autenticado, rol, cargando } = useAuth();

  if (cargando) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center text-ink/60 font-mono text-sm">
        Cargando...
      </div>
    );
  }

  if (!autenticado) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(rol)) return <Navigate to="/" replace />;

  return children;
}

export default RequireRole;
