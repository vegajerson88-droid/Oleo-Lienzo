import { useEffect, useRef, useState } from "react";
import { Bot, Loader2, MessageSquare, Send, Sparkles, X } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { useSesionChat } from "../hooks/useSesionChat";
import { api } from "../services/api";

const SALUDO = {
  rol: "asistente",
  contenido:
    "¡Hola! Soy el asistente de Óleo & Lienzo. Puedo contarte sobre nuestras obras, " +
    "los servicios de enmarcado y envío, el proceso de compra, o ayudarte a radicar " +
    "una PQR. ¿En qué te ayudo?",
};

const SUGERENCIAS = [
  "¿Qué obras tienen disponibles?",
  "¿Cómo compro una obra?",
  "¿Hacen envíos a todo el país?",
  "Quiero radicar una PQR",
];

/**
 * Chatbot flotante de atención al cliente.
 *
 * Funciona con y sin sesión iniciada. Cuando el backend no tiene configurada
 * la clave de IA, la respuesta llega del modo local y la interfaz lo indica
 * con una etiqueta, en lugar de hacerla pasar por generada por IA.
 */
function ChatbotWidget() {
  const { token } = useAuth();
  const sessionId = useSesionChat();

  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState([SALUDO]);
  const [borrador, setBorrador] = useState("");
  const [enviando, setEnviando] = useState(false);

  const finRef = useRef(null);
  const entradaRef = useRef(null);

  // Mantiene la vista al final al llegar mensajes nuevos.
  useEffect(() => {
    if (abierto) finRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes, abierto, enviando]);

  useEffect(() => {
    if (abierto) entradaRef.current?.focus();
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;
    const alPulsar = (evento) => {
      if (evento.key === "Escape") setAbierto(false);
    };
    window.addEventListener("keydown", alPulsar);
    return () => window.removeEventListener("keydown", alPulsar);
  }, [abierto]);

  async function enviar(texto) {
    const mensaje = (texto ?? borrador).trim();
    if (!mensaje || enviando) return;

    setMensajes((actuales) => [...actuales, { rol: "usuario", contenido: mensaje }]);
    setBorrador("");
    setEnviando(true);

    try {
      const respuesta = await api.enviarMensajeChat(mensaje, sessionId, token);
      setMensajes((actuales) => [
        ...actuales,
        {
          rol: "asistente",
          contenido: respuesta.respuesta,
          generadoPorIa: respuesta.generado_por_ia,
          modelo: respuesta.modelo,
        },
      ]);
    } catch (error) {
      setMensajes((actuales) => [
        ...actuales,
        {
          rol: "asistente",
          contenido:
            error.status === 0
              ? "No consigo conectar con el servidor. Comprueba que el backend esté en marcha."
              : `No pude responder en este momento. ${error.message}`,
          esError: true,
        },
      ]);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      {/* Lanzador */}
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        aria-label={abierto ? "Cerrar el asistente" : "Abrir el asistente virtual"}
        aria-expanded={abierto}
        className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center
                   rounded-full bg-forest text-paper shadow-alta transition-transform
                   hover:scale-105 active:scale-95"
      >
        {abierto ? <X size={24} /> : <MessageSquare size={24} />}
        {!abierto && (
          <span
            className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center
                       rounded-full bg-gold"
            aria-hidden="true"
          >
            <Sparkles size={10} className="text-forest-dark" />
          </span>
        )}
      </button>

      {/* Ventana de conversación */}
      {abierto && (
        <div
          role="dialog"
          aria-label="Asistente virtual de Óleo & Lienzo"
          className="fixed inset-x-0 bottom-0 z-40 flex h-[85vh] flex-col overflow-hidden
                     rounded-t-2xl border border-line bg-paper shadow-alta
                     animate-deslizar-arriba
                     sm:inset-x-auto sm:bottom-24 sm:right-5 sm:h-[520px] sm:w-[380px]
                     sm:rounded-2xl"
        >
          <header className="flex items-center gap-3 border-b-2 border-gold bg-forest px-4 py-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gold/20">
              <Bot size={18} className="text-gold" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-display text-sm text-paper">Asistente Óleo &amp; Lienzo</p>
              <p className="etiqueta text-paper/60">Atención al cliente</p>
            </div>
            <button
              type="button"
              onClick={() => setAbierto(false)}
              aria-label="Cerrar"
              className="rounded-lg p-1 text-paper/70 transition-colors hover:bg-white/10 hover:text-paper sm:hidden"
            >
              <X size={20} />
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto bg-wall/40 px-4 py-4">
            {mensajes.map((mensaje, indice) => {
              const esUsuario = mensaje.rol === "usuario";
              return (
                <div
                  key={indice}
                  className={`flex ${esUsuario ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed
                      ${esUsuario
                        ? "rounded-br-sm bg-forest text-paper"
                        : mensaje.esError
                        ? "rounded-bl-sm border border-error/30 bg-error-suave text-error"
                        : "rounded-bl-sm border border-line bg-paper text-ink"}`}
                  >
                    <p className="whitespace-pre-wrap">{mensaje.contenido}</p>

                    {/* Se declara si respondió la IA o el modo local. */}
                    {mensaje.generadoPorIa !== undefined && (
                      <p
                        className={`mt-1.5 flex items-center gap-1 font-mono text-[9px] uppercase
                          tracking-wider ${mensaje.generadoPorIa ? "text-gold" : "text-muted"}`}
                      >
                        <Sparkles size={9} aria-hidden="true" />
                        {mensaje.generadoPorIa
                          ? `Generado con IA · ${mensaje.modelo ?? ""}`
                          : "Respuesta local"}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}

            {enviando && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm border
                                border-line bg-paper px-3.5 py-2.5 text-sm text-muted">
                  <Loader2 size={14} className="animate-spin" aria-hidden="true" />
                  Escribiendo…
                </div>
              </div>
            )}

            {/* Atajos, solo mientras la conversación no ha empezado. */}
            {mensajes.length === 1 && !enviando && (
              <div className="flex flex-wrap gap-2 pt-1">
                {SUGERENCIAS.map((sugerencia) => (
                  <button
                    key={sugerencia}
                    type="button"
                    onClick={() => enviar(sugerencia)}
                    className="rounded-full border border-line bg-paper px-3 py-1.5 text-xs
                               text-ink-soft transition-colors hover:border-gold hover:bg-gold/10"
                  >
                    {sugerencia}
                  </button>
                ))}
              </div>
            )}

            <div ref={finRef} />
          </div>

          <form
            onSubmit={(evento) => {
              evento.preventDefault();
              enviar();
            }}
            className="flex items-end gap-2 border-t border-line bg-paper p-3"
          >
            <label htmlFor="chat-entrada" className="sr-only">
              Escribe tu mensaje
            </label>
            <input
              id="chat-entrada"
              ref={entradaRef}
              value={borrador}
              onChange={(evento) => setBorrador(evento.target.value)}
              placeholder="Escribe tu pregunta…"
              maxLength={1000}
              disabled={enviando}
              className="min-w-0 flex-1 rounded-full border border-line bg-white px-4 py-2.5
                         text-sm placeholder:text-muted/60 focus:border-gold focus:outline-none
                         focus:ring-2 focus:ring-gold/40 disabled:bg-paper-dim"
            />
            <button
              type="submit"
              disabled={enviando || !borrador.trim()}
              aria-label="Enviar mensaje"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full
                         bg-forest text-paper transition-colors hover:bg-forest-dark
                         disabled:cursor-not-allowed disabled:bg-muted/40"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default ChatbotWidget;
