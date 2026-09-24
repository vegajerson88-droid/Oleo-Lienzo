/**
 * Tabla responsiva.
 *
 * En pantallas anchas es una tabla normal; por debajo de `sm` cada fila se
 * convierte en una tarjeta con las cabeceras repetidas delante de cada dato,
 * que es lo único que se lee bien en un móvil.
 */
function Table({ columnas, filas, claveFila, alPulsarFila, className = "" }) {
  return (
    <div className={`w-full ${className}`}>
      {/* Escritorio y tablet */}
      <div className="hidden overflow-x-auto sm:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-line">
              {columnas.map((columna) => (
                <th
                  key={columna.clave}
                  scope="col"
                  className={`whitespace-nowrap px-3 py-3 etiqueta font-semibold text-muted
                    ${columna.alinear === "derecha" ? "text-right"
                      : columna.alinear === "centro" ? "text-center" : "text-left"}`}
                >
                  {columna.titulo}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filas.map((fila, indice) => (
              <tr
                key={claveFila ? claveFila(fila) : indice}
                onClick={alPulsarFila ? () => alPulsarFila(fila) : undefined}
                className={`border-b border-line/50 transition-colors last:border-0
                  ${indice % 2 === 1 ? "bg-paper-dim/40" : ""}
                  ${alPulsarFila ? "cursor-pointer hover:bg-gold/8" : "hover:bg-paper-dim/70"}`}
              >
                {columnas.map((columna) => (
                  <td
                    key={columna.clave}
                    className={`px-3 py-3 align-middle
                      ${columna.alinear === "derecha" ? "text-right"
                        : columna.alinear === "centro" ? "text-center" : "text-left"}
                      ${columna.className ?? ""}`}
                  >
                    {columna.render ? columna.render(fila) : fila[columna.clave]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Móvil: una tarjeta por fila */}
      <ul className="flex flex-col gap-3 sm:hidden">
        {filas.map((fila, indice) => (
          <li
            key={claveFila ? claveFila(fila) : indice}
            onClick={alPulsarFila ? () => alPulsarFila(fila) : undefined}
            className={`rounded-lg border border-line/70 bg-paper p-3.5
              ${alPulsarFila ? "cursor-pointer active:bg-gold/8" : ""}`}
          >
            {columnas
              .filter((columna) => !columna.ocultarEnMovil)
              .map((columna) => (
                <div
                  key={columna.clave}
                  className="flex items-start justify-between gap-3 border-b border-line/40
                             py-1.5 last:border-0"
                >
                  <span className="etiqueta shrink-0 text-muted">{columna.titulo}</span>
                  <span className="min-w-0 text-right text-sm">
                    {columna.render ? columna.render(fila) : fila[columna.clave]}
                  </span>
                </div>
              ))}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Table;
