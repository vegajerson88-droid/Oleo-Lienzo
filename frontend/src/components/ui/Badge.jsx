import { AlertTriangle, Ban, CheckCircle2, Clock, HelpCircle, RotateCcw, Truck } from "lucide-react";

/**
 * Insignia de estado.
 *
 * El color nunca viaja solo: cada insignia lleva siempre su icono y su texto,
 * de modo que el estado se distingue sin depender de la percepción del color.
 */
const TONOS = {
  exito: "bg-exito-suave text-exito border-exito/25",
  aviso: "bg-aviso-suave text-aviso border-aviso/25",
  error: "bg-error-suave text-error border-error/25",
  info: "bg-info-suave text-info border-info/25",
  neutro: "bg-paper-dim text-muted border-line",
};

/** Cada estado del dominio, con su tono, su icono y su texto legible. */
const ESTADOS = {
  // Pedidos
  pendiente: { tono: "aviso", icono: Clock, texto: "Pendiente" },
  confirmado: { tono: "info", icono: CheckCircle2, texto: "Confirmado" },
  entregado: { tono: "exito", icono: Truck, texto: "Entregado" },
  cancelado: { tono: "error", icono: Ban, texto: "Cancelado" },
  // Ventas
  pendiente_pago: { tono: "aviso", icono: Clock, texto: "Pendiente de pago" },
  pagada: { tono: "exito", icono: CheckCircle2, texto: "Pagada" },
  anulada: { tono: "error", icono: Ban, texto: "Anulada" },
  reembolsada: { tono: "error", icono: RotateCcw, texto: "Reembolsada" },
  // Facturas
  emitida: { tono: "info", icono: CheckCircle2, texto: "Emitida" },
  // PQR
  en_proceso: { tono: "info", icono: Clock, texto: "En proceso" },
  respondida: { tono: "exito", icono: CheckCircle2, texto: "Respondida" },
  cerrada: { tono: "neutro", icono: CheckCircle2, texto: "Cerrada" },
  // Tipos de PQR
  peticion: { tono: "info", icono: HelpCircle, texto: "Petición" },
  queja: { tono: "aviso", icono: AlertTriangle, texto: "Queja" },
  reclamo: { tono: "error", icono: AlertTriangle, texto: "Reclamo" },
  sugerencia: { tono: "neutro", icono: HelpCircle, texto: "Sugerencia" },
  // Usuarios
  activo: { tono: "exito", icono: CheckCircle2, texto: "Activo" },
  inactivo: { tono: "neutro", icono: Ban, texto: "Inactivo" },
  // Roles
  administrador: { tono: "info", icono: CheckCircle2, texto: "Administrador" },
  empleado: { tono: "aviso", icono: CheckCircle2, texto: "Empleado" },
  cliente: { tono: "neutro", icono: CheckCircle2, texto: "Cliente" },
};

function Badge({ estado, texto, tono, icono: IconoManual, className = "" }) {
  const config = ESTADOS[estado] ?? {};
  const Icono = IconoManual ?? config.icono ?? null;
  const tonoFinal = tono ?? config.tono ?? "neutro";
  const etiqueta = texto ?? config.texto ?? estado ?? "—";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1
        font-mono text-[10px] uppercase tracking-wider whitespace-nowrap
        ${TONOS[tonoFinal]} ${className}`}
    >
      {Icono && <Icono size={11} className="shrink-0" aria-hidden="true" />}
      {etiqueta}
    </span>
  );
}

export default Badge;
