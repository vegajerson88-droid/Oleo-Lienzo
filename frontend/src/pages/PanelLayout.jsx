import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, LogOut, Menu, X } from "lucide-react";

import Logo from "../components/Logo";
import { useAuth } from "../context/AuthContext";

/**
 * Estructura de los tres paneles: barra lateral fija y área de trabajo.
 *
 * Los paneles viven fuera de la estructura pública del sitio —sin cabecera ni
 * pie— porque son una herramienta de gestión, no una página de catálogo. En su
 * lugar hay un enlace explícito para volver a la galería.
 *
 * En pantallas estrechas la barra se convierte en un cajón que se abre con el
 * botón de menú; en escritorio queda siempre a la vista.
 */
function PanelLayout({ titulo, descripcion, pestanas, activa, onCambiar, children }) {
  const { usuario, rol, logout } = useAuth();
  const [cajonAbierto, setCajonAbierto] = useState(false);

  const seccion = pestanas.find((p) => p.id === activa);

  // Al cambiar de sección en móvil, el cajón estorba: se cierra solo.
  useEffect(() => {
    setCajonAbierto(false);
  }, [activa]);

  // Con el cajón abierto, el fondo no debe poder desplazarse.
  useEffect(() => {
    if (!cajonAbierto) return undefined;
    const previo = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previo;
    };
  }, [cajonAbierto]);

  // Escape cierra el cajón, como cualquier diálogo.
  useEffect(() => {
    if (!cajonAbierto) return undefined;
    const alPulsar = (evento) => evento.key === "Escape" && setCajonAbierto(false);
    window.addEventListener("keydown", alPulsar);
    return () => window.removeEventListener("keydown", alPulsar);
  }, [cajonAbierto]);

  const barraLateral = (
    <div className="flex h-full flex-col bg-forest-dark text-paper">
      {/* Identidad y vuelta al sitio público */}
      <div className="border-b border-paper/10 px-5 py-5">
        <Link to="/" className="inline-block" aria-label="Ir a la galería">
          <Logo tamano="sm" />
        </Link>
      </div>

      {/* Quién ha iniciado sesión */}
      <div className="flex items-center gap-3 border-b border-paper/10 px-5 py-4">
        <span
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full
                     bg-gold/15 font-display text-base text-gold"
          aria-hidden="true"
        >
          {usuario?.nombre?.charAt(0)?.toUpperCase()}
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-paper">
            {usuario?.nombre} {usuario?.apellido}
          </p>
          <p className="truncate etiqueta text-gold/80">{rol}</p>
        </div>
      </div>

      {/* Secciones del panel */}
      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Secciones del panel">
        <ul className="space-y-1">
          {pestanas.map(({ id, label, icono: Icono }) => {
            const activo = id === activa;
            return (
              <li key={id}>
                <button
                  type="button"
                  onClick={() => onCambiar(id)}
                  aria-current={activo ? "page" : undefined}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left
                              text-sm transition-colors ${
                                activo
                                  ? "bg-gold text-forest-dark font-medium"
                                  : "text-paper/75 hover:bg-paper/10 hover:text-paper"
                              }`}
                >
                  {Icono && <Icono size={17} aria-hidden="true" className="shrink-0" />}
                  <span className="truncate">{label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Salidas: a la galería o de la sesión */}
      <div className="space-y-1 border-t border-paper/10 px-3 py-4">
        <Link
          to="/"
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-paper/75
                     transition-colors hover:bg-paper/10 hover:text-paper"
        >
          <ArrowLeft size={17} aria-hidden="true" className="shrink-0" />
          Volver al inicio
        </Link>
        <button
          type="button"
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm
                     text-paper/75 transition-colors hover:bg-error/20 hover:text-paper"
        >
          <LogOut size={17} aria-hidden="true" className="shrink-0" />
          Cerrar sesión
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-paper-dim lg:flex">
      {/* Barra lateral fija en escritorio */}
      <aside className="hidden w-64 shrink-0 lg:block">
        <div className="fixed inset-y-0 left-0 w-64">{barraLateral}</div>
      </aside>

      {/* Cajón en móvil */}
      {cajonAbierto && (
        <>
          <div
            className="fixed inset-0 z-40 bg-ink/50 lg:hidden"
            onClick={() => setCajonAbierto(false)}
            aria-hidden="true"
          />
          <div className="fixed inset-y-0 left-0 z-50 w-64 shadow-media lg:hidden">
            {barraLateral}
          </div>
        </>
      )}

      {/* Área de trabajo */}
      <div className="min-w-0 flex-1">
        {/* Barra superior: solo en móvil, para abrir el cajón */}
        <div className="flex items-center gap-3 border-b border-line bg-paper px-4 py-3 lg:hidden">
          <button
            type="button"
            onClick={() => setCajonAbierto(true)}
            aria-label="Abrir el menú del panel"
            aria-expanded={cajonAbierto}
            className="rounded-lg border border-line p-2 text-ink-soft transition-colors
                       hover:border-forest hover:text-forest"
          >
            {cajonAbierto ? <X size={18} /> : <Menu size={18} />}
          </button>
          <span className="truncate font-display text-lg">{seccion?.label ?? titulo}</span>
        </div>

        <main className="px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
          <header className="mb-7">
            <span className="etiqueta text-sienna">Panel de {rol}</span>
            <h1 className="mt-1.5 font-display text-2xl sm:text-3xl">{titulo}</h1>
            <p className="mt-1.5 max-w-3xl text-sm text-muted">{descripcion}</p>
          </header>

          {children}
        </main>
      </div>
    </div>
  );
}

export default PanelLayout;
