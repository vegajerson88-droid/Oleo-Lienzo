/** Contenedor básico de contenido, con cabecera y acciones opcionales. */
function Card({ titulo, descripcion, acciones, icono: Icono, className = "", children, ...props }) {
  const tieneCabecera = titulo || acciones;

  return (
    <section className={`tarjeta overflow-hidden ${className}`} {...props}>
      {tieneCabecera && (
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-line/70 px-5 py-4">
          <div className="min-w-0">
            <h3 className="flex items-center gap-2 font-display text-base text-ink">
              {Icono && <Icono size={16} className="text-gold shrink-0" aria-hidden="true" />}
              {titulo}
            </h3>
            {descripcion && <p className="mt-0.5 text-xs text-muted">{descripcion}</p>}
          </div>
          {acciones && <div className="flex shrink-0 flex-wrap gap-2">{acciones}</div>}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export default Card;
