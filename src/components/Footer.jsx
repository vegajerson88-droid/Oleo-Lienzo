import { Link } from "react-router-dom";
import { Mail } from "lucide-react";

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

const enlaces = [
  { to: "/", label: "Inicio" },
  { to: "/quienes-somos", label: "¿Quiénes Somos?" },
  { to: "/contacto", label: "Contacto" },
  { to: "/login", label: "Iniciar sesión" },
];

const redes = [
  { href: "https://instagram.com", label: "Instagram", Icon: InstagramIcon },
  { href: "https://facebook.com", label: "Facebook", Icon: FacebookIcon },
  { href: "https://twitter.com", label: "Twitter / X", Icon: TwitterIcon },
  { href: "mailto:contacto@oleoylienzo.com", label: "Correo", Icon: Mail },
];

function Footer() {
  return (
    <footer className="bg-forest-dark text-paper mt-16">
      <div className="container mx-auto max-w-6xl px-6 py-12 grid grid-cols-1 sm:grid-cols-3 gap-10">
        <div>
          <h3 className="font-display text-lg mb-4">Óleo &amp; Lienzo</h3>
          <ul className="space-y-2.5">
            {enlaces.map((e) => (
              <li key={e.to}>
                <Link
                  to={e.to}
                  className="text-sm text-paper/75 hover:text-gold transition-colors"
                >
                  {e.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="font-mono text-xs uppercase tracking-wider text-gold mb-4">
            Sobre nosotros
          </h3>
          <p className="text-sm text-paper/75 leading-relaxed">
            Galería de arte contemporáneo especializada en piezas originales
            de pintores colombianos. Acompañamos a coleccionistas y artistas
            desde 2015, con envíos certificados a todo el país.
          </p>
        </div>

        <div>
          <h3 className="font-mono text-xs uppercase tracking-wider text-gold mb-4">
            Síguenos
          </h3>
          <div className="flex gap-3">
            {redes.map(({ href, label, Icon }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                aria-label={label}
                className="w-9 h-9 flex items-center justify-center rounded-full border border-paper/25 text-paper/75 hover:border-gold hover:text-gold transition-colors"
              >
                <Icon className="w-4 h-4" />
              </a>
            ))}
          </div>
          <p className="text-sm text-paper/60 mt-5">
            Calle 45 # 12-30, Bogotá D.C.
            <br />
            +57 300 123 4567
          </p>
        </div>
      </div>

      <div className="border-t border-white/10">
        <p className="text-center text-xs font-mono text-paper/50 py-5">
          &copy; {new Date().getFullYear()} Óleo &amp; Lienzo. Todos los derechos reservados.
        </p>
      </div>
    </footer>
  );
}

export default Footer;
