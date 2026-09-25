import { useState } from "react";

import { formatoMoneda, formatoNumero } from "./utilidades";

/**
 * Gráfico de barras horizontales para comparar magnitudes entre categorías.
 *
 * Es de **serie única**: todas las barras comparten el mismo tono y la
 * identidad de cada una la da su etiqueta, no el color. Por eso no necesita
 * leyenda y se lee igual con cualquier tipo de daltonismo.
 *
 * Se eligen barras horizontales porque las etiquetas del proyecto son largas
 * ("Primavera Fragmentada — Camila Duarte") y en vertical quedarían giradas.
 */
function GraficoBarras({ puntos = [], formato = "numero", alto = 220 }) {
  const [activo, setActivo] = useState(null);

  if (puntos.length === 0) {
    return (
      <p className="flex items-center justify-center text-sm text-muted" style={{ height: alto }}>
        Sin datos para el periodo seleccionado.
      </p>
    );
  }

  const maximo = Math.max(...puntos.map((p) => p.valor), 1);
  const formatear = (v) => (formato === "moneda" ? formatoMoneda(v) : formatoNumero(v));

  return (
    <div>
      <ul className="flex flex-col gap-2.5">
        {puntos.map((punto, indice) => {
          const porcentaje = Math.max((punto.valor / maximo) * 100, 1.5);
          const esActivo = activo === indice;

          return (
            <li
              key={`${punto.etiqueta}-${indice}`}
              className="group"
              onMouseEnter={() => setActivo(indice)}
              onMouseLeave={() => setActivo(null)}
              onFocus={() => setActivo(indice)}
              onBlur={() => setActivo(null)}
            >
              <div className="mb-1 flex items-baseline justify-between gap-3">
                <span className="truncate text-xs text-ink-soft" title={punto.etiqueta}>
                  {punto.etiqueta}
                </span>
                {/* Etiqueta directa: el valor va siempre visible, sin depender del hover. */}
                <span className="shrink-0 font-mono text-xs tabular-nums text-ink">
                  {formatear(punto.valor)}
                </span>
              </div>

              {/* La pista de fondo da la referencia del máximo. */}
              <div
                className="h-2.5 w-full overflow-hidden rounded-full bg-line/50"
                role="img"
                aria-label={`${punto.etiqueta}: ${formatear(punto.valor)}`}
                tabIndex={0}
              >
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${porcentaje}%`,
                    backgroundColor: "var(--color-grafico)",
                    opacity: activo === null || esActivo ? 1 : 0.45,
                  }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default GraficoBarras;
