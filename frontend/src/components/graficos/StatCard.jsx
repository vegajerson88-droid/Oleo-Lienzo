import { TrendingDown, TrendingUp } from "lucide-react";

import { formatearValor } from "./utilidades";

/**
 * Tarjeta de indicador.
 *
 * Cuando hay dato de variación, la flecha y el texto la acompañan: la
 * dirección nunca se comunica solo con el color.
 */
function StatCard({ etiqueta, valor, formato = "numero", variacion, icono: Icono, cargando }) {
  if (cargando) {
    return (
      <div className="tarjeta p-4">
        <div className="animate-brillo space-y-2.5">
          <div className="h-2.5 w-2/3 rounded bg-line/60" />
          <div className="h-7 w-1/2 rounded bg-line/60" />
        </div>
      </div>
    );
  }

  const subio = typeof variacion === "number" && variacion > 0;
  const bajo = typeof variacion === "number" && variacion < 0;
  const FlechaTendencia = subio ? TrendingUp : TrendingDown;

  return (
    <div className="tarjeta group relative overflow-hidden p-4 transition-shadow hover:shadow-media">
      {/* Filete superior dorado: firma visual de la marca. */}
      <span className="absolute inset-x-0 top-0 h-[3px] bg-gold" aria-hidden="true" />

      <div className="flex items-start justify-between gap-3">
        <p className="etiqueta text-muted">{etiqueta}</p>
        {Icono && (
          <Icono size={16} className="shrink-0 text-gold/70" aria-hidden="true" />
        )}
      </div>

      <p className="mt-2 font-display text-2xl font-semibold tabular-nums text-forest">
        {formatearValor(valor, formato)}
      </p>

      {(subio || bajo) && (
        <p
          className={`mt-1.5 flex items-center gap-1 font-mono text-[11px] tabular-nums
            ${subio ? "text-exito" : "text-error"}`}
        >
          <FlechaTendencia size={12} aria-hidden="true" />
          {Math.abs(variacion).toFixed(1)}%
          <span className="text-muted">frente a la semana anterior</span>
        </p>
      )}
    </div>
  );
}

export default StatCard;
