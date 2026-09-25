import { ChevronLeft, ChevronRight } from "lucide-react";

/** Controles de paginación con el rango visible descrito en texto. */
function Pagination({ pagina, tamanoPagina, total, onCambiar, className = "" }) {
  const totalPaginas = Math.max(1, Math.ceil(total / tamanoPagina));
  if (total === 0) return null;

  const desde = (pagina - 1) * tamanoPagina + 1;
  const hasta = Math.min(pagina * tamanoPagina, total);

  const botonBase =
    "flex items-center gap-1 rounded-lg border border-line px-3 py-1.5 etiqueta " +
    "transition-colors enabled:hover:border-forest enabled:hover:bg-forest/5 " +
    "disabled:cursor-not-allowed disabled:text-muted/50 disabled:border-line/50";

  return (
    <nav
      aria-label="Paginación"
      className={`flex flex-wrap items-center justify-between gap-3 border-t border-line/70
                  pt-4 ${className}`}
    >
      <p className="text-xs text-muted">
        Mostrando <span className="font-medium text-ink tabular-nums">{desde}–{hasta}</span> de{" "}
        <span className="font-medium text-ink tabular-nums">{total}</span>
      </p>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onCambiar(pagina - 1)}
          disabled={pagina <= 1}
          className={botonBase}
        >
          <ChevronLeft size={14} aria-hidden="true" />
          Anterior
        </button>
        <span className="etiqueta tabular-nums text-muted" aria-current="page">
          {pagina} / {totalPaginas}
        </span>
        <button
          type="button"
          onClick={() => onCambiar(pagina + 1)}
          disabled={pagina >= totalPaginas}
          className={botonBase}
        >
          Siguiente
          <ChevronRight size={14} aria-hidden="true" />
        </button>
      </div>
    </nav>
  );
}

export default Pagination;
