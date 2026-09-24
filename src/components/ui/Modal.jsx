import { useEffect, useRef } from "react";
import { X } from "lucide-react";

const ANCHOS = { sm: "max-w-md", md: "max-w-lg", lg: "max-w-2xl", xl: "max-w-4xl" };

/**
 * Ventana modal accesible.
 *
 * Cierra con Escape y al pulsar fuera, bloquea el desplazamiento del fondo,
 * lleva el foco al diálogo al abrirse y lo devuelve al cerrarse.
 */
function Modal({ abierto, onCerrar, titulo, descripcion, ancho = "md", pie, children }) {
  const dialogoRef = useRef(null);
  const focoPrevioRef = useRef(null);

  useEffect(() => {
    if (!abierto) return;

    focoPrevioRef.current = document.activeElement;
    const overflowOriginal = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialogoRef.current?.focus();

    const alPulsarTecla = (evento) => {
      if (evento.key === "Escape") onCerrar?.();
    };
    window.addEventListener("keydown", alPulsarTecla);

    return () => {
      document.body.style.overflow = overflowOriginal;
      window.removeEventListener("keydown", alPulsarTecla);
      focoPrevioRef.current?.focus?.();
    };
  }, [abierto, onCerrar]);

  if (!abierto) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-ink/55 p-0
                 backdrop-blur-sm animate-aparecer sm:items-center sm:p-4"
      onMouseDown={(evento) => {
        if (evento.target === evento.currentTarget) onCerrar?.();
      }}
    >
      <div
        ref={dialogoRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-titulo"
        aria-describedby={descripcion ? "modal-descripcion" : undefined}
        tabIndex={-1}
        className={`flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-2xl bg-paper
          shadow-alta outline-none animate-deslizar-arriba sm:rounded-2xl ${ANCHOS[ancho]}`}
      >
        <header className="flex items-start justify-between gap-4 border-b border-line/70 px-5 py-4">
          <div className="min-w-0">
            <h2 id="modal-titulo" className="font-display text-lg text-ink">
              {titulo}
            </h2>
            {descripcion && (
              <p id="modal-descripcion" className="mt-0.5 text-xs text-muted">
                {descripcion}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onCerrar}
            aria-label="Cerrar"
            className="-mr-1 shrink-0 rounded-lg p-1 text-muted transition-colors
                       hover:bg-error-suave hover:text-error"
          >
            <X size={20} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-5">{children}</div>

        {pie && (
          <footer className="flex flex-wrap justify-end gap-3 border-t border-line/70
                             bg-paper-dim/60 px-5 py-4">
            {pie}
          </footer>
        )}
      </div>
    </div>
  );
}

export default Modal;
