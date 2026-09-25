import { Link } from "react-router-dom";
import { Clock, Mail, MapPin, Phone } from "lucide-react";

import Logo from "./Logo";

function InstagramIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

function FacebookIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M14 9h3V6h-3c-2 0-3 1.2-3 3v2H9v3h2v6h3v-6h2.5l.5-3H14V9.6c0-.4.2-.6.6-.6Z" />
    </svg>
  );
}

function TwitterIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M4 4l7.5 9.5L4.5 20H7l5.5-5.5L17 20h3l-8-9.8L19 4h-2.5l-5 5-4-5H4Z" />
    </svg>
  );
}

const NAVEGACION = [
  { to: "/", label: "Galería" },
  { to: "/catalogo", label: "Catálogo" },
  { to: "/quienes-somos", label: "¿Quiénes Somos?" },
  { to: "/contacto", label: "Contacto" },
  { to: "/login", label: "Iniciar sesión" },
];

const REDES = [
  { href: "https://instagram.com", label: "Instagram", Icono: InstagramIcon },
  { href: "https://facebook.com", label: "Facebook", Icono: FacebookIcon },
  { href: "https://twitter.com", label: "Twitter / X", Icono: TwitterIcon },
  { href: "mailto:contacto@oleoylienzo.com", label: "Correo", Icono: Mail },
];

const CONTACTO = [
  { Icono: MapPin, texto: "Calle 45 # 12-30, Bogotá D.C." },
  { Icono: Clock, texto: "Martes a sábado, 10:00 a.m. – 6:00 p.m." },
  { Icono: Phone, texto: "+57 300 123 4567" },
  { Icono: Mail, texto: "contacto@oleoylienzo.com" },
];

function Footer() {
  return (
    <footer className="bg-forest-dark text-paper">
      <div className="contenedor grid grid-cols-1 gap-10 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2 lg:col-span-1">
          <Logo tamano="sm" />
          <p className="mt-4 text-sm leading-relaxed text-paper/70">
            Galería de arte contemporáneo especializada en piezas originales de
            pintores colombianos. Acompañamos a coleccionistas y artistas desde 2015.
          </p>
        </div>

        <nav aria-label="Enlaces del pie de página">
          <h3 className="mb-4 etiqueta text-gold">Navegación</h3>
          <ul className="space-y-2.5">
            {NAVEGACION.map((enlace) => (
              <li key={enlace.to}>
                <Link
                  to={enlace.to}
                  className="text-sm text-paper/70 transition-colors hover:text-gold"
                >
                  {enlace.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div>
          <h3 className="mb-4 etiqueta text-gold">Visítanos</h3>
          <ul className="space-y-2.5">
            {CONTACTO.map(({ Icono, texto }) => (
              <li key={texto} className="flex items-start gap-2.5 text-sm text-paper/70">
                <Icono size={15} className="mt-0.5 shrink-0 text-gold/60" aria-hidden="true" />
                {texto}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="mb-4 etiqueta text-gold">Síguenos</h3>
          <div className="flex gap-3">
            {REDES.map(({ href, label, Icono }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                aria-label={label}
                className="flex h-10 w-10 items-center justify-center rounded-full border
                           border-paper/25 text-paper/70 transition-colors
                           hover:border-gold hover:text-gold"
              >
                <Icono className="h-4 w-4" />
              </a>
            ))}
          </div>
          <p className="mt-5 text-xs leading-relaxed text-paper/50">
            Todas nuestras piezas son originales e incluyen certificado de
            autenticidad firmado por su artista.
          </p>
        </div>
      </div>

      <div className="border-t border-white/10">
        <p className="contenedor py-5 text-center font-mono text-[11px] text-paper/45">
          &copy; {new Date().getFullYear()} Óleo &amp; Lienzo S.A.S. · NIT 901.234.567-8 ·
          Todos los derechos reservados.
        </p>
      </div>
    </footer>
  );
}

export default Footer;
