import { useState } from "react";
import { api } from "../../services/api";
import Button from "../../components/ui/Button";

const ESTADO_COLOR = {
  ok: "text-forest",
  no_disponible: "text-ink/50",
  no_configurado: "text-ink/50",
  error: "text-sienna",
};

function Diagnostico({ token }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  async function ejecutar() {
    setCargando(true);
    setError("");
    try {
      const resultado = await api.diagnostico(token);
      setData(resultado);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="bg-paper border border-ink/10 rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-lg">Diagnóstico del sistema</h3>
        <Button variant="outline" onClick={ejecutar} disabled={cargando}>
          {cargando ? "Consultando..." : "Ejecutar diagnóstico"}
        </Button>
      </div>
      {error && <p className="text-sm text-sienna">{error}</p>}
      {data && (
        <div>
          <p className="text-sm mb-3">
            Estado general:{" "}
            <span className={data.estado_general === "ok" ? "text-forest font-medium" : "text-sienna font-medium"}>
              {data.estado_general}
            </span>
          </p>
          <ul className="flex flex-col gap-2">
            {Object.entries(data.componentes).map(([nombre, comp]) => (
              <li key={nombre} className="flex items-center justify-between text-sm border-b border-ink/10 pb-2">
                <span className="capitalize">{nombre.replace(/_/g, " ")}</span>
                <span className={ESTADO_COLOR[comp.estado] || ""}>
                  {comp.estado} ({comp.latencia_ms} ms)
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default Diagnostico;
