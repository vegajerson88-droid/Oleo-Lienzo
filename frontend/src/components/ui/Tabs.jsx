/** Pestañas de navegación dentro de los paneles. */
function Tabs({ pestanas, activa, onCambiar, className = "" }) {
  return (
    <div
      role="tablist"
      aria-label="Secciones del panel"
      className={`-mx-1 flex gap-1 overflow-x-auto border-b border-line px-1 ${className}`}
    >
      {pestanas.map(({ id, label, icono: Icono, contador }) => {
        const esActiva = activa === id;
        return (
          <button
            key={id}
            role="tab"
            type="button"
            aria-selected={esActiva}
            onClick={() => onCambiar(id)}
            className={`flex shrink-0 items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3
              etiqueta transition-colors
              ${esActiva
                ? "border-gold text-forest"
                : "border-transparent text-muted hover:border-line hover:text-ink"}`}
          >
            {Icono && <Icono size={14} aria-hidden="true" />}
            {label}
            {contador !== undefined && contador !== null && (
              <span
                className={`rounded-full px-1.5 py-0.5 text-[10px] tabular-nums
                  ${esActiva ? "bg-gold/20 text-forest" : "bg-line/70 text-muted"}`}
              >
                {contador}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default Tabs;
