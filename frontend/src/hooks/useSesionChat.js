import { useState } from "react";

const CLAVE = "oleo_lienzo_chat_session";

/** Identificador estable de la conversación del chatbot en este navegador. */
export function useSesionChat() {
  const [sessionId] = useState(() => {
    try {
      const guardado = localStorage.getItem(CLAVE);
      if (guardado) return guardado;
    } catch {
      /* almacenamiento bloqueado: se genera uno solo para esta carga */
    }

    const nuevo =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `sesion-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

    try {
      localStorage.setItem(CLAVE, nuevo);
    } catch {
      /* sin persistencia, la conversación no sobrevive a la recarga */
    }
    return nuevo;
  });

  return sessionId;
}
