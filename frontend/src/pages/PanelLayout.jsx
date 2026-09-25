import Tabs from "../components/ui/Tabs";
import { useAuth } from "../context/AuthContext";

/**
 * Estructura común de los tres paneles.
 *
 * Unifica cabecera, saludo, distintivo de rol y pestañas, para que
 * administrador, empleado y cliente compartan la misma forma aunque
 * cada uno vea contenidos distintos.
 */
function PanelLayout({ titulo, descripcion, pestanas, activa, onCambiar, children }) {
  const { usuario, rol } = useAuth();

  return (
    <div className="contenedor py-8 sm:py-10">
      <header className="mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <span className="etiqueta text-sienna">Panel de {rol}</span>
            <h1 className="mt-1.5 font-display text-2xl sm:text-3xl">{titulo}</h1>
            <p className="mt-1.5 text-sm text-muted">{descripcion}</p>
          </div>

          <div className="flex items-center gap-3 rounded-xl border border-line/70 bg-paper px-4 py-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full
                             bg-forest font-display text-base text-gold">
              {usuario?.nombre?.charAt(0)?.toUpperCase()}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {usuario?.nombre} {usuario?.apellido}
              </p>
              <p className="truncate text-xs text-muted">{usuario?.email}</p>
            </div>
          </div>
        </div>
      </header>

      <Tabs pestanas={pestanas} activa={activa} onCambiar={onCambiar} className="mb-6" />

      {children}
    </div>
  );
}

export default PanelLayout;
