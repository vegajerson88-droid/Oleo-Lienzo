import { useState } from "react";
import { Activity, Bot, CreditCard, Database, Mail, RefreshCw, Sparkles } from "lucide-react";

import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import { useToast } from "../../context/ToastContext";
import { api } from "../../services/api";

const COMPONENTES = {
  base_de_datos: { etiqueta: "Base de datos PostgreSQL", icono: Database },
  ia_local: { etiqueta: "Modelo de IA local", icono: Sparkles },
  ia_externa: { etiqueta: "IA externa (Groq)", icono: Bot },
  pasarela_pago: { etiqueta: "Pasarela de pago (Stripe)", icono: CreditCard },
  correo: { etiqueta: "Correo saliente (SMTP)", icono: Mail },
};

const ESTADOS = {
  ok: { clases: "border-exito/30 bg-exito-suave text-exito", texto: "Operativo" },
  error: { clases: "border-error/30 bg-error-suave text-error", texto: "Con error" },
  no_configurado: { clases: "border-line bg-paper-dim text-muted", texto: "Sin configurar" },
  no_disponible: { clases: "border-line bg-paper-dim text-muted", texto: "No disponible" },
};

/**
 * Diagnóstico del sistema.
 *
 * Cada componente se comprueba de verdad contra su servicio: una consulta a
 * PostgreSQL, una llamada a Groq, el balance de Stripe y una conexión SMTP.
 * No es un endpoint que devuelva «ok» sin mirar nada.
 */
function Diagnostico({ token }) {
  const toast = useToast();
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  async function ejecutar() {
    setCargando(true);
    setError("");
    try {
      const resultado = await api.diagnostico(token);
      setDatos(resultado);
      toast[resultado.estado_general === "ok" ? "exito" : "aviso"](
        `Diagnóstico completado: ${resultado.estado_general}.`
      );
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <Card
      titulo="Diagnóstico del sistema"
      descripcion="Comprueba en vivo cada dependencia del backend."
      icono={Activity}
      acciones={
        <Button
          size="sm" variant="secundario" iconoIzquierda={RefreshCw}
          cargando={cargando} onClick={ejecutar}
        >
          {datos ? "Volver a comprobar" : "Ejecutar diagnóstico"}
        </Button>
      }
    >
      {error && <Alert tipo="error" className="mb-4">{error}</Alert>}

      {!datos && !cargando && !error && (
        <div className="py-10 text-center">
          <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full
                           border border-line bg-paper-dim text-muted">
            <Activity size={24} aria-hidden="true" />
          </span>
          <p className="text-sm text-ink-soft">
            Pulsa «Ejecutar diagnóstico» para comprobar la base de datos, la IA,
            la pasarela de pago y el correo.
          </p>
        </div>
      )}

      {datos && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg
                          border border-line/70 bg-paper-dim/50 p-4">
            <div>
              <p className="etiqueta text-muted">Estado general</p>
              <p
                className={`mt-0.5 font-display text-xl ${
                  datos.estado_general === "ok" ? "text-exito" : "text-error"
                }`}
              >
                {datos.estado_general === "ok" ? "Todo en orden" : "Servicio degradado"}
              </p>
            </div>
            <div className="text-right">
              <p className="etiqueta text-muted">Entorno</p>
              <p className="mt-0.5 font-mono text-sm">
                {datos.entorno} · v{datos.version}
              </p>
            </div>
          </div>

          <ul className="space-y-3">
            {Object.entries(datos.componentes).map(([clave, componente]) => {
              const meta = COMPONENTES[clave] ?? { etiqueta: clave, icono: Activity };
              const estado = ESTADOS[componente.estado] ?? ESTADOS.no_disponible;
              const Icono = meta.icono;

              return (
                <li
                  key={clave}
                  className="flex flex-wrap items-start justify-between gap-3 rounded-lg
                             border border-line/70 p-4"
                >
                  <div className="flex min-w-0 items-start gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center
                                     rounded-lg bg-paper-dim text-forest">
                      <Icono size={16} aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <p className="font-medium text-sm">{meta.etiqueta}</p>
                      {componente.detalle && (
                        <p className="mt-0.5 break-words text-xs text-muted">
                          {componente.detalle}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-3">
                    <span className="font-mono text-xs tabular-nums text-muted">
                      {componente.latencia_ms} ms
                    </span>
                    <span
                      className={`rounded-full border px-2.5 py-1 font-mono text-[10px]
                                  uppercase tracking-wider ${estado.clases}`}
                    >
                      {estado.texto}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>

          <Alert tipo="info">
            «Sin configurar» no es un fallo: son integraciones opcionales que se
            activan rellenando sus variables en el archivo <code>.env</code> del
            backend.
          </Alert>
        </div>
      )}
    </Card>
  );
}

export default Diagnostico;
