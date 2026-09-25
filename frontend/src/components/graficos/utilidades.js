/** Utilidades compartidas por los gráficos. */

/** Formatea un importe en pesos colombianos, abreviando los valores grandes. */
export function formatoMoneda(valor, { compacto = false } = {}) {
  const numero = Number(valor) || 0;
  if (compacto) {
    if (Math.abs(numero) >= 1_000_000) return `$${(numero / 1_000_000).toFixed(1)}M`;
    if (Math.abs(numero) >= 1_000) return `$${Math.round(numero / 1_000)}k`;
  }
  return numero.toLocaleString("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  });
}

export function formatoNumero(valor) {
  return (Number(valor) || 0).toLocaleString("es-CO");
}

export function formatoPorcentaje(valor) {
  const numero = Number(valor) || 0;
  return `${numero > 0 ? "+" : ""}${numero.toFixed(1)}%`;
}

/** Convierte 2026-09-24 en "24 sep" para los ejes. */
export function etiquetaFecha(iso) {
  const fecha = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(fecha.getTime())) return iso;
  return fecha.toLocaleDateString("es-CO", { day: "numeric", month: "short" });
}

/** Elige el formateador según el tipo de dato del indicador. */
export function formatearValor(valor, formato) {
  if (formato === "moneda") return formatoMoneda(valor);
  if (formato === "porcentaje") return formatoPorcentaje(valor);
  return formatoNumero(valor);
}
