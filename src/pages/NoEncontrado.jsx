import { Link } from "react-router-dom";
import { ArrowLeft, Frame } from "lucide-react";

/** Página 404 con la identidad de la galería. */
function NoEncontrado() {
  return (
    <div className="contenedor flex min-h-[60vh] flex-col items-center justify-center py-16 text-center">
      <span className="mb-6 flex h-20 w-20 items-center justify-center rounded-full
                       border-2 border-gold/40 text-gold">
        <Frame size={34} aria-hidden="true" />
      </span>
      <p className="etiqueta text-sienna">Error 404</p>
      <h1 className="mb-3 mt-2 font-display text-3xl sm:text-4xl">Esta sala está vacía</h1>
      <p className="mb-8 max-w-md text-sm text-ink-soft">
        La página que buscas no existe o cambió de sitio. Vuelve a la galería
        para seguir recorriendo la colección.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 rounded-lg bg-forest px-6 py-3.5 etiqueta
                   text-paper transition-colors hover:bg-forest-dark"
      >
        <ArrowLeft size={14} aria-hidden="true" />
        Volver a la galería
      </Link>
    </div>
  );
}

export default NoEncontrado;
