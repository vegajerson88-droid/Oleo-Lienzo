import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Info, TriangleAlert, X } from "lucide-react";

const ToastContext = createContext(null);

const TIPOS = {
  exito: { clases: "border-exito/30 bg-exito-suave text-exito", icono: CheckCircle2 },
  error: { clases: "border-error/30 bg-error-suave text-error", icono: AlertCircle },
  aviso: { clases: "border-aviso/30 bg-aviso-suave text-aviso", icono: TriangleAlert },
  info: { clases: "border-info/30 bg-info-suave text-info", icono: Info },
};

const DURACION_POR_DEFECTO = 4500;

/**
 * Avisos emergentes de toda la aplicación.
 *
 * Evita que cada pantalla invente su propia forma de confirmar una acción o
 * de informar de un error. Los errores permanecen más tiempo en pantalla
 * porque suelen requerir que el usuario haga algo.
 */
export function ToastProvider({ children }) {
  const [avisos, setAvisos] = useState([]);
  const temporizadores = useRef(new Map());

  const cerrar = useCallback((id) => {
    setAvisos((actuales) => actuales.filter((a) => a.id !== id));
    const temporizador = temporizadores.current.get(id);
    if (temporizador) {
      clearTimeout(temporizador);
      temporizadores.current.delete(id);
    }
  }, []);

  const mostrar = useCallback(
    (mensaje, tipo = "info", duracion) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const milisegundos = duracion ?? (tipo === "error" ? 7000 : DURACION_POR_DEFECTO);
      setAvisos((actuales) => [...actuales, { id, mensaje, tipo }]);
      temporizadores.current.set(id, setTimeout(() => cerrar(id), milisegundos));
      return id;
    },
    [cerrar]
  );

  const valor = useMemo(
    () => ({
      mostrar,
      exito: (mensaje, duracion) => mostrar(mensaje, "exito", duracion),
      error: (mensaje, duracion) => mostrar(mensaje, "error", duracion),
      aviso: (mensaje, duracion) => mostrar(mensaje, "aviso", duracion),
      info: (mensaje, duracion) => mostrar(mensaje, "info", duracion),
      cerrar,
    }),
    [mostrar, cerrar]
  );

  return (
    <ToastContext.Provider value={valor}>
      {children}

      {/* `aria-live` hace que los lectores de pantalla anuncien cada aviso. */}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed inset-x-0 bottom-0 z-[60] flex flex-col items-center
                   gap-2 p-4 sm:inset-x-auto sm:right-0 sm:top-0 sm:items-end"
      >
        {avisos.map(({ id, mensaje, tipo }) => {
          const { clases, icono: Icono } = TIPOS[tipo] ?? TIPOS.info;
          return (
            <div
              key={id}
              role={tipo === "error" ? "alert" : "status"}
              className={`pointer-events-auto flex w-full max-w-sm items-start gap-2.5 rounded-lg
                border px-4 py-3 shadow-alta animate-deslizar-arriba ${clases}`}
            >
              <Icono size={17} className="mt-0.5 shrink-0" aria-hidden="true" />
              <p className="min-w-0 flex-1 text-sm">{mensaje}</p>
              <button
                type="button"
                onClick={() => cerrar(id)}
                aria-label="Cerrar aviso"
                className="-mr-1 shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
              >
                <X size={15} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const contexto = useContext(ToastContext);
  if (!contexto) throw new Error("useToast debe usarse dentro de <ToastProvider>");
  return contexto;
}
