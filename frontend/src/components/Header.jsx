import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { LayoutDashboard, LogOut, Menu, User, X } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import Logo from "./Logo";

const ENLACES = [
  { to: "/", label: "Galería", end: true },
  { to: "/catalogo", label: "Catálogo" },
  { to: "/quienes-somos", label: "Quiénes Somos" },
  { to: "/contacto", label: "Contacto" },
];

function Header() {
  const [menuAbierto, setMenuAbierto] = useState(false);
  const { autenticado, usuario, rol, rutaPanel, logout } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();

  // Cierra el menú móvil al cambiar de página.
  useEffect(() => setMenuAbierto(false), [ubicacion.pathname]);

  // Bloquea el desplazamiento del fondo mientras el menú móvil está abierto.
  useEffect(() => {
    document.body.style.overflow = menuAbierto ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuAbierto]);

  const claseEnlace = ({ isActive }) =>
    `etiqueta border-b-2 pb-1 transition-colors ${
      isActive ? "border-gold text-paper" : "border-transparent text-paper/70 hover:text-paper"
    }`;

  function cerrarSesion() {
    logout();
    setMenuAbierto(false);
    navegar("/");
  }

  const etiquetaPanel = rol === "cliente" ? "Mi cuenta" : "Panel";

  return (
    <header className="sticky top-0 z-30 border-b-[3px] border-gold bg-forest text-paper">
      <div className="contenedor flex items-center justify-between py-3.5">
        <NavLink to="/" aria-label="Óleo & Lienzo, ir al inicio">
          <Logo />
        </NavLink>

        {/* Navegación de escritorio */}
        <nav className="hidden items-center gap-7 lg:flex" aria-label="Navegación principal">
          {ENLACES.map((enlace) => (
            <NavLink key={enlace.to} to={enlace.to} end={enlace.end} className={claseEnlace}>
              {enlace.label}
            </NavLink>
          ))}

          {autenticado ? (
            <div className="flex items-center gap-4 border-l border-paper/20 pl-6">
              <NavLink
                to={rutaPanel}
                className="flex items-center gap-2 etiqueta text-paper/80 transition-colors hover:text-gold"
              >
                <LayoutDashboard size={14} aria-hidden="true" />
                {etiquetaPanel}
              </NavLink>

              {/* Requisito del tercer avance: el nombre del usuario en el Navbar. */}
              <span className="etiqueta text-gold">Hola, {usuario?.nombre}</span>

              <button
                type="button"
                onClick={cerrarSesion}
                className="flex items-center gap-2 rounded-lg border border-gold/50 px-3 py-2
                           etiqueta text-paper/85 transition-colors
                           hover:border-gold hover:bg-gold hover:text-forest-dark"
              >
                <LogOut size={14} aria-hidden="true" />
                Salir
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="flex items-center gap-2 rounded-lg border border-gold bg-gold/10 px-4 py-2
                         etiqueta text-gold transition-colors hover:bg-gold hover:text-forest-dark"
            >
              <User size={14} aria-hidden="true" />
              Ingresar
            </NavLink>
          )}
        </nav>

        <button
          type="button"
          className="rounded-lg p-1 text-paper lg:hidden"
          onClick={() => setMenuAbierto((v) => !v)}
          aria-label={menuAbierto ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={menuAbierto}
        >
          {menuAbierto ? <X size={26} /> : <Menu size={26} />}
        </button>
      </div>

      {/* Navegación móvil */}
      {menuAbierto && (
        <nav
          className="max-h-[calc(100vh-64px)] overflow-y-auto border-t border-gold/25 bg-forest
                     px-4 pb-6 sm:px-6 lg:hidden"
          aria-label="Navegación móvil"
        >
          {autenticado && (
            <p className="border-b border-white/10 py-4 etiqueta text-gold">
              Hola, {usuario?.nombre} · {rol}
            </p>
          )}

          {ENLACES.map((enlace) => (
            <NavLink
              key={enlace.to}
              to={enlace.to}
              end={enlace.end}
              className={({ isActive }) =>
                `block border-b border-white/10 py-3.5 etiqueta ${
                  isActive ? "text-gold" : "text-paper/80"
                }`
              }
            >
              {enlace.label}
            </NavLink>
          ))}

          {autenticado ? (
            <>
              <NavLink
                to={rutaPanel}
                className="flex items-center gap-2 border-b border-white/10 py-3.5 etiqueta text-paper/80"
              >
                <LayoutDashboard size={14} aria-hidden="true" />
                {etiquetaPanel}
              </NavLink>
              <button
                type="button"
                onClick={cerrarSesion}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border
                           border-gold px-3 py-3 etiqueta text-gold"
              >
                <LogOut size={14} aria-hidden="true" />
                Cerrar sesión
              </button>
            </>
          ) : (
            <NavLink
              to="/login"
              className="mt-4 flex items-center justify-center gap-2 rounded-lg bg-gold px-3 py-3
                         etiqueta font-semibold text-forest-dark"
            >
              <User size={14} aria-hidden="true" />
              Ingresar
            </NavLink>
          )}
        </nav>
      )}
    </header>
  );
}

export default Header;
