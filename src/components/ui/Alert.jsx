import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react";

const TIPOS = {
  exito: { clases: "bg-exito-suave border-exito/30 text-exito", icono: CheckCircle2 },
  error: { clases: "bg-error-suave border-error/30 text-error", icono: AlertCircle },
  aviso: { clases: "bg-aviso-suave border-aviso/30 text-aviso", icono: TriangleAlert },
  info: { clases: "bg-info-suave border-info/30 text-info", icono: Info },
};

/** Mensaje en línea. El icono acompaña siempre al color, nunca al revés. */
function Alert({ tipo = "info", titulo, children, className = "" }) {
  const { clases, icono: Icono } = TIPOS[tipo] ?? TIPOS.info;

  return (
    <div
      role={tipo === "error" ? "alert" : "status"}
      className={`flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm ${clases} ${className}`}
    >
      <Icono size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        {titulo && <p className="font-semibold">{titulo}</p>}
        {children && <div className={titulo ? "mt-0.5 opacity-90" : ""}>{children}</div>}
      </div>
    </div>
  );
}

export default Alert;
