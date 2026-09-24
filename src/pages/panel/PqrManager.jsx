import { useState } from "react";
import { MessageSquareWarning, Reply } from "lucide-react";

import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Modal from "../../components/ui/Modal";
import Pagination from "../../components/ui/Pagination";
import Select from "../../components/ui/Select";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import Textarea from "../../components/ui/Textarea";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";
import { validateField } from "../../utils/validators";

const TAMANO_PAGINA = 10;

const ESTADOS = [
  { value: "", label: "Todos los estados" },
  { value: "pendiente", label: "Pendientes" },
  { value: "en_proceso", label: "En proceso" },
  { value: "respondida", label: "Respondidas" },
  { value: "cerrada", label: "Cerradas" },
];

const TIPOS = [
  { value: "", label: "Todos los tipos" },
  { value: "peticion", label: "Peticiones" },
  { value: "queja", label: "Quejas" },
  { value: "reclamo", label: "Reclamos" },
  { value: "sugerencia", label: "Sugerencias" },
];

/** Transiciones válidas, espejo de la máquina de estados del backend. */
const TRANSICIONES = {
  pendiente: ["en_proceso", "cerrada"],
  en_proceso: ["cerrada"],
  respondida: ["cerrada", "en_proceso"],
  cerrada: [],
};

const ETIQUETA_ACCION = {
  en_proceso: "Poner en proceso",
  cerrada: "Cerrar",
};

/** Gestión de PQR. El cliente solo ve las suyas y no puede responder. */
function PqrManager({ token, puedeGestionar = false }) {
  const toast = useToast();

  const [pagina, setPagina] = useState(1);
  const [estado, setEstado] = useState("");
  const [tipo, setTipo] = useState("");
  const [respondiendo, setRespondiendo] = useState(null);
  const [respuesta, setRespuesta] = useState("");
  const [errorRespuesta, setErrorRespuesta] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [cambiando, setCambiando] = useState(null);

  const pqrs = useRecurso(
    (signal) =>
      api.listarPqr(
        token,
        {
          page: pagina, page_size: TAMANO_PAGINA,
          estado: estado || undefined, tipo: tipo || undefined,
        },
        signal
      ),
    [pagina, estado, tipo]
  );

  async function enviarRespuesta(evento) {
    evento.preventDefault();
    const error = validateField("respuesta", respuesta);
    setErrorRespuesta(error);
    if (error) return;

    setEnviando(true);
    try {
      await api.responderPqr(respondiendo.id, respuesta.trim(), token);
      toast.exito(`Respondiste la PQR ${respondiendo.radicado}. Se notificó al cliente.`);
      setRespondiendo(null);
      setRespuesta("");
      pqrs.recargar();
    } catch (fallo) {
      setErrorRespuesta(fallo.message);
    } finally {
      setEnviando(false);
    }
  }

  async function cambiarEstado(pqr, nuevoEstado) {
    setCambiando(`${pqr.id}-${nuevoEstado}`);
    try {
      await api.cambiarEstadoPqr(pqr.id, nuevoEstado, token);
      toast.exito(`${pqr.radicado}: ${nuevoEstado.replace("_", " ")}.`);
      pqrs.recargar();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setCambiando(null);
    }
  }

  return (
    <>
      <Card
        titulo={`PQR${pqrs.datos ? ` (${pqrs.datos.total})` : ""}`}
        descripcion={
          puedeGestionar
            ? "Peticiones, quejas, reclamos y sugerencias de los clientes."
            : "Tus solicitudes y el estado en que se encuentran."
        }
        icono={MessageSquareWarning}
        acciones={
          <div className="flex gap-2">
            <div className="w-40">
              <Select
                name="estado" value={estado} options={ESTADOS}
                onChange={(evento) => {
                  setEstado(evento.target.value);
                  setPagina(1);
                }}
              />
            </div>
            <div className="w-40">
              <Select
                name="tipo" value={tipo} options={TIPOS}
                onChange={(evento) => {
                  setTipo(evento.target.value);
                  setPagina(1);
                }}
              />
            </div>
          </div>
        }
      >
        {pqrs.cargando ? (
          <SkeletonFilas filas={4} />
        ) : pqrs.error ? (
          <Alert tipo="error">{pqrs.error.message}</Alert>
        ) : pqrs.datos.items.length === 0 ? (
          <EmptyState
            icono={MessageSquareWarning}
            titulo="No hay solicitudes"
            descripcion={
              puedeGestionar
                ? "Las PQR que radiquen los clientes aparecerán aquí."
                : "Puedes radicar una desde la página de contacto."
            }
          />
        ) : (
          <>
            <ul className="flex flex-col gap-4">
              {pqrs.datos.items.map((pqr) => (
                <li key={pqr.id} className="rounded-lg border border-line/70 bg-paper-dim/30 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-sm font-medium">{pqr.radicado}</span>
                        <Badge estado={pqr.tipo} />
                        <Badge estado={pqr.estado} />
                      </p>
                      <p className="mt-1.5 font-display text-base">{pqr.asunto}</p>
                      <p className="mt-0.5 text-xs text-muted">
                        {pqr.contacto_nombre} · {pqr.contacto_email} ·{" "}
                        {new Date(pqr.creado_en).toLocaleDateString("es-CO", { dateStyle: "medium" })}
                      </p>
                    </div>
                  </div>

                  <p className="mt-3 whitespace-pre-wrap border-t border-line/60 pt-3 text-sm text-ink-soft">
                    {pqr.mensaje}
                  </p>

                  {pqr.respuesta && (
                    <div className="mt-3 rounded-lg border-l-[3px] border-gold bg-paper p-3">
                      <p className="etiqueta text-gold">Respuesta de la galería</p>
                      <p className="mt-1.5 whitespace-pre-wrap text-sm text-ink-soft">
                        {pqr.respuesta}
                      </p>
                      {pqr.respondido_en && (
                        <p className="mt-2 text-xs text-muted">
                          {new Date(pqr.respondido_en).toLocaleString("es-CO", {
                            dateStyle: "medium", timeStyle: "short",
                          })}
                        </p>
                      )}
                    </div>
                  )}

                  {puedeGestionar && (
                    <div className="mt-4 flex flex-wrap gap-2 border-t border-line/60 pt-3">
                      {pqr.estado !== "cerrada" && (
                        <Button
                          size="sm" iconoIzquierda={Reply}
                          onClick={() => {
                            setRespondiendo(pqr);
                            setRespuesta(pqr.respuesta ?? "");
                            setErrorRespuesta("");
                          }}
                        >
                          {pqr.respuesta ? "Editar respuesta" : "Responder"}
                        </Button>
                      )}
                      {(TRANSICIONES[pqr.estado] ?? []).map((destino) => (
                        <Button
                          key={destino} size="sm" variant="secundario"
                          cargando={cambiando === `${pqr.id}-${destino}`}
                          onClick={() => cambiarEstado(pqr, destino)}
                        >
                          {ETIQUETA_ACCION[destino] ?? destino}
                        </Button>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>

            <Pagination
              pagina={pagina} tamanoPagina={TAMANO_PAGINA}
              total={pqrs.datos.total} onCambiar={setPagina} className="mt-5"
            />
          </>
        )}
      </Card>

      <Modal
        abierto={Boolean(respondiendo)}
        onCerrar={() => setRespondiendo(null)}
        titulo={respondiendo ? `Responder ${respondiendo.radicado}` : ""}
        descripcion="El cliente recibirá la respuesta por correo."
        pie={
          <>
            <Button variant="fantasma" onClick={() => setRespondiendo(null)} disabled={enviando}>
              Cancelar
            </Button>
            <Button type="submit" form="formulario-respuesta" cargando={enviando}>
              Enviar respuesta
            </Button>
          </>
        }
      >
        {respondiendo && (
          <form id="formulario-respuesta" onSubmit={enviarRespuesta} noValidate>
            <div className="mb-4 rounded-lg bg-paper-dim/60 p-3">
              <p className="etiqueta text-muted">Solicitud original</p>
              <p className="mt-1 font-medium text-sm">{respondiendo.asunto}</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-ink-soft">
                {respondiendo.mensaje}
              </p>
            </div>

            <Textarea
              label="Tu respuesta" name="respuesta" rows={6}
              value={respuesta} onChange={(evento) => setRespuesta(evento.target.value)}
              error={errorRespuesta} maxLength={2000} contador required
            />
          </form>
        )}
      </Modal>
    </>
  );
}

export default PqrManager;
