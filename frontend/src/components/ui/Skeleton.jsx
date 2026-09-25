/** Marcador de carga: ocupa el sitio del contenido para evitar saltos. */
function Skeleton({ className = "", ...props }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-brillo rounded-md bg-line/60 ${className}`}
      {...props}
    />
  );
}

/** Varias filas de marcadores, para tablas y listas que están cargando. */
export function SkeletonFilas({ filas = 4, className = "" }) {
  return (
    <div className={`flex flex-col gap-3 ${className}`} role="status" aria-label="Cargando…">
      {Array.from({ length: filas }).map((_, indice) => (
        <div key={indice} className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 shrink-0 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-2/5" />
            <Skeleton className="h-2.5 w-3/5" />
          </div>
          <Skeleton className="h-7 w-20 shrink-0" />
        </div>
      ))}
      <span className="sr-only">Cargando contenido…</span>
    </div>
  );
}

export default Skeleton;
