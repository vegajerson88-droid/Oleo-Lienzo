import { useMemo, useRef, useState } from "react";

import { etiquetaFecha, formatoMoneda, formatoNumero } from "./utilidades";

const MARGEN = { arriba: 14, derecha: 14, abajo: 26, izquierda: 52 };
const ANCHO = 560;
const ALTO = 220;

/**
 * Gráfico lineal de una sola serie para la evolución en el tiempo.
 *
 * Incluye la capa de interacción que exige un gráfico en pantalla: al mover
 * el ratón aparece una línea guía vertical, se resalta el punto más cercano y
 * un recuadro muestra su fecha y su valor exactos. Debajo hay una vista de
 * tabla plegable, para lectores de pantalla y para quien prefiera las cifras.
 */
function GraficoLinea({ puntos = [], formato = "moneda" }) {
  const svgRef = useRef(null);
  const [indiceActivo, setIndiceActivo] = useState(null);
  const [verTabla, setVerTabla] = useState(false);

  const formatear = (v) => (formato === "moneda" ? formatoMoneda(v) : formatoNumero(v));

  const { coordenadas, maximo, rutaLinea, rutaArea } = useMemo(() => {
    if (puntos.length === 0) return { coordenadas: [], maximo: 0, rutaLinea: "", rutaArea: "" };

    const max = Math.max(...puntos.map((p) => p.valor), 1);
    const anchoUtil = ANCHO - MARGEN.izquierda - MARGEN.derecha;
    const altoUtil = ALTO - MARGEN.arriba - MARGEN.abajo;
    const paso = puntos.length > 1 ? anchoUtil / (puntos.length - 1) : 0;

    const coords = puntos.map((punto, indice) => ({
      ...punto,
      x: MARGEN.izquierda + (puntos.length > 1 ? indice * paso : anchoUtil / 2),
      y: MARGEN.arriba + altoUtil - (punto.valor / max) * altoUtil,
    }));

    const linea = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");
    const area =
      coords.length > 0
        ? `${linea} L ${coords.at(-1).x} ${ALTO - MARGEN.abajo} L ${coords[0].x} ${ALTO - MARGEN.abajo} Z`
        : "";

    return { coordenadas: coords, maximo: max, rutaLinea: linea, rutaArea: area };
  }, [puntos]);

  if (puntos.length === 0) {
    return (
      <p className="flex h-[220px] items-center justify-center text-sm text-muted">
        Sin datos para el periodo seleccionado.
      </p>
    );
  }

  /** Busca el punto cuyo eje X está más cerca del cursor. */
  function alMover(evento) {
    const svg = svgRef.current;
    if (!svg) return;
    const caja = svg.getBoundingClientRect();
    const x = ((evento.clientX - caja.left) / caja.width) * ANCHO;
    let masCercano = 0;
    let distanciaMinima = Infinity;
    coordenadas.forEach((c, i) => {
      const distancia = Math.abs(c.x - x);
      if (distancia < distanciaMinima) {
        distanciaMinima = distancia;
        masCercano = i;
      }
    });
    setIndiceActivo(masCercano);
  }

  const activo = indiceActivo !== null ? coordenadas[indiceActivo] : null;
  const lineasGuia = [0, 0.5, 1];

  return (
    <div>
      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${ANCHO} ${ALTO}`}
          className="w-full touch-none"
          style={{ height: ALTO }}
          role="img"
          aria-label={`Evolución: ${puntos.length} puntos, máximo ${formatear(maximo)}`}
          onMouseMove={alMover}
          onMouseLeave={() => setIndiceActivo(null)}
        >
          {/* Rejilla discreta: orienta sin competir con los datos. */}
          {lineasGuia.map((fraccion) => {
            const y = MARGEN.arriba + (ALTO - MARGEN.arriba - MARGEN.abajo) * fraccion;
            return (
              <g key={fraccion}>
                <line
                  x1={MARGEN.izquierda} y1={y} x2={ANCHO - MARGEN.derecha} y2={y}
                  stroke="var(--color-line)" strokeWidth="1"
                />
                <text
                  x={MARGEN.izquierda - 8} y={y + 3.5} textAnchor="end"
                  className="fill-muted font-mono" style={{ fontSize: 9 }}
                >
                  {formato === "moneda"
                    ? formatoMoneda(maximo * (1 - fraccion), { compacto: true })
                    : Math.round(maximo * (1 - fraccion))}
                </text>
              </g>
            );
          })}

          {/* Relleno tenue bajo la línea: da volumen sin tapar la rejilla. */}
          <path d={rutaArea} fill="var(--color-grafico)" opacity="0.1" />

          {/* La serie: 2 px, uniones redondeadas. */}
          <path
            d={rutaLinea}
            fill="none"
            stroke="var(--color-grafico)"
            strokeWidth="2"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Línea guía vertical del punto activo. */}
          {activo && (
            <line
              x1={activo.x} y1={MARGEN.arriba} x2={activo.x} y2={ALTO - MARGEN.abajo}
              stroke="var(--color-forest)" strokeWidth="1" strokeDasharray="3 3" opacity="0.4"
            />
          )}

          {/* Marcadores con anillo del color de la superficie, para que no se fundan. */}
          {coordenadas.map((c, i) => (
            <circle
              key={i}
              cx={c.x} cy={c.y}
              r={indiceActivo === i ? 5.5 : 3.5}
              fill="var(--color-grafico)"
              stroke="var(--color-paper)"
              strokeWidth="2"
              className="transition-all duration-150"
            />
          ))}

          {/* Eje X: solo el primero, el del medio y el último, para no amontonar. */}
          {coordenadas.map((c, i) => {
            const mostrar =
              i === 0 || i === coordenadas.length - 1 || i === Math.floor(coordenadas.length / 2);
            if (!mostrar) return null;
            return (
              <text
                key={`x-${i}`}
                x={c.x} y={ALTO - 8}
                textAnchor={i === 0 ? "start" : i === coordenadas.length - 1 ? "end" : "middle"}
                className="fill-muted font-mono" style={{ fontSize: 9 }}
              >
                {etiquetaFecha(c.etiqueta)}
              </text>
            );
          })}
        </svg>

        {/* Recuadro flotante con el dato exacto. */}
        {activo && (
          <div
            className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-lg border
                       border-line bg-paper px-3 py-2 shadow-media"
            style={{
              left: `${(activo.x / ANCHO) * 100}%`,
              top: `${(activo.y / ALTO) * 100}%`,
              transform: "translate(-50%, -125%)",
            }}
          >
            <p className="etiqueta whitespace-nowrap text-muted">{etiquetaFecha(activo.etiqueta)}</p>
            <p className="whitespace-nowrap font-mono text-sm font-bold tabular-nums text-forest">
              {formatear(activo.valor)}
            </p>
          </div>
        )}
      </div>

      {/* Vista de tabla: misma información, accesible y copiable. */}
      <details className="mt-3" open={verTabla} onToggle={(e) => setVerTabla(e.target.open)}>
        <summary className="cursor-pointer etiqueta text-muted hover:text-forest">
          Ver los datos como tabla
        </summary>
        <table className="mt-2 w-full text-xs">
          <thead>
            <tr className="border-b border-line">
              <th scope="col" className="py-1.5 text-left etiqueta text-muted">Fecha</th>
              <th scope="col" className="py-1.5 text-right etiqueta text-muted">Valor</th>
            </tr>
          </thead>
          <tbody>
            {puntos.map((punto, i) => (
              <tr key={i} className="border-b border-line/40 last:border-0">
                <td className="py-1.5">{etiquetaFecha(punto.etiqueta)}</td>
                <td className="py-1.5 text-right font-mono tabular-nums">
                  {formatear(punto.valor)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}

export default GraficoLinea;
