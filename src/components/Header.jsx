import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { Menu, X, User, LogOut, LayoutDashboard } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/", label: "Galería", end: true },
  { to: "/quienes-somos", label: "Quiénes Somos" },
  { to: "/contacto", label: "Contacto" },
];

function Header() {
  const [open, setOpen] = useState(false);
  const { autenticado, usuario, rol, logout } = useAuth();
  const navigate = useNavigate();

  const linkClass = ({ isActive }) =>
    `font-mono text-xs uppercase tracking-wider border-b-2 pb-1 transition-colors ${
      isActive
        ? "border-gold text-paper"
        : "border-transparent text-paper/75 hover:text-paper"
    }`;

  const handleLogout = () => {
    logout();
    setOpen(false);
    navigate("/");
  };

  return (
    <header className="bg-forest text-paper border-b-[3px] border-gold">
      <div className="container mx-auto max-w-6xl px-6 flex items-center justify-between py-4">
        <NavLink to="/" className="flex items-center gap-3">
          <span className="flex items-center justify-center w-9 h-9 rounded-full border-2 border-gold font-display italic text-gold">
            O
          </span>
          <span className="font-display text-xl">
            Óleo<span className="text-gold italic px-0.5">&amp;</span>Lienzo
          </span>
        </NavLink>

        <nav className="hidden md:flex items-center gap-7" aria-label="Navegación principal">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
              {l.label}
            </NavLink>
          ))}

          {autenticado ? (
            <div className="flex items-center gap-4">
              {(rol === "administrador" || rol === "empleado") && (
                <NavLink
                  to={rol === "administrador" ? "/panel/administrador" : "/panel/empleado"}
                  className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-paper/85 hover:text-gold"
                >
                  <LayoutDashboard size={14} />
                  Panel
                </NavLink>
              )}
              {rol === "cliente" && (
                <NavLink
                  to="/panel/cliente"
                  className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-paper/85 hover:text-gold"
                >
                  <LayoutDashboard size={14} />
                  Mis pedidos
                </NavLink>
              )}
              <span className="font-mono text-xs uppercase tracking-wider text-gold">
                Hola, {usuario?.nombre}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider border border-gold/60 text-paper/85 px-3 py-2 rounded-md hover:bg-gold hover:text-forest-dark hover:border-gold transition-colors"
              >
                <LogOut size={14} />
                Salir
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider bg-gold/10 border border-gold text-gold px-3 py-2 rounded-md hover:bg-gold hover:text-forest-dark transition-colors"
            >
              <User size={14} />
              Ingresar
            </NavLink>
          )}
        </nav>

        <button
          className="md:hidden text-paper"
          onClick={() => setOpen((o) => !o)}
          aria-label={open ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={open}
        >
          {open ? <X size={26} /> : <Menu size={26} />}
        </button>
      </div>

      {open && (
        <nav
          className="md:hidden flex flex-col gap-1 px-6 pb-5 bg-forest border-t border-gold/30"
          aria-label="Navegación móvil"
        >
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `font-mono text-xs uppercase tracking-wider py-3 border-b border-white/10 ${
                  isActive ? "text-gold" : "text-paper/80"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}

          {autenticado ? (
            <>
              {(rol === "administrador" || rol === "empleado" || rol === "cliente") && (
                <NavLink
                  to={
                    rol === "administrador"
                      ? "/panel/administrador"
                      : rol === "empleado"
                      ? "/panel/empleado"
                      : "/panel/cliente"
                  }
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2 py-3 border-b border-white/10 text-paper/80 font-mono text-xs uppercase tracking-wider"
                >
                  <LayoutDashboard size={14} />
                  Mi panel
                </NavLink>
              )}
              <span className="py-3 font-mono text-xs uppercase tracking-wider text-gold">
                Hola, {usuario?.nombre}
              </span>
              <button
                onClick={handleLogout}
                className="mt-1 flex items-center justify-center gap-2 font-mono text-xs uppercase tracking-wider border border-gold text-gold px-3 py-2.5 rounded-md"
              >
                <LogOut size={14} />
                Salir
              </button>
            </>
          ) : (
            <NavLink
              to="/login"
              onClick={() => setOpen(false)}
              className="mt-3 flex items-center justify-center gap-2 font-mono text-xs uppercase tracking-wider border border-gold text-gold px-3 py-2.5 rounded-md"
            >
              <User size={14} />
              Ingresar
            </NavLink>
          )}
        </nav>
      )}
    </header>
  );
}

export default Header;
