import { Inbox } from "lucide-react";

/** Estado vacío: explica por qué no hay nada y ofrece la acción siguiente. */
function EmptyState({ icono: Icono = Inbox, titulo, descripcion, accion, className = "" }) {
  return (
    <div className={`flex flex-col items-center justify-center px-6 py-12 text-center ${className}`}>
      <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-full
                       border border-line bg-paper-dim text-muted">
        <Icono size={24} aria-hidden="true" />
      </span>
      <p className="font-display text-base text-ink">{titulo}</p>
      {descripcion && (
        <p className="mt-1.5 max-w-sm text-sm text-muted">{descripcion}</p>
      )}
      {accion && <div className="mt-5">{accion}</div>}
    </div>
  );
}

export default EmptyState;
