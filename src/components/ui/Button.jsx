import { Loader2 } from "lucide-react";

const VARIANTES = {
  primario:
    "bg-forest text-paper hover:bg-forest-dark active:bg-forest-dark shadow-suave " +
    "disabled:bg-muted/40 disabled:text-paper disabled:shadow-none",
  secundario:
    "bg-paper text-forest border border-forest/30 hover:border-forest hover:bg-forest/5 " +
    "disabled:text-muted disabled:border-line",
  oro:
    "bg-gold text-forest-dark hover:bg-gold-soft shadow-suave font-semibold " +
    "disabled:bg-gold/40 disabled:shadow-none",
  fantasma:
    "text-forest hover:bg-forest/8 disabled:text-muted",
  peligro:
    "bg-error/10 text-error border border-error/30 hover:bg-error hover:text-paper " +
    "disabled:opacity-50",
};

const TAMANOS = {
  sm: "px-3 py-1.5 text-[11px] gap-1.5",
  md: "px-5 py-2.5 text-xs gap-2",
  lg: "px-7 py-3.5 text-sm gap-2.5",
};

/**
 * Botón reutilizable de la aplicación.
 *
 * Mientras `cargando` es true muestra un spinner y se deshabilita solo, para
 * que ninguna pantalla tenga que implementar su propio estado de envío.
 */
function Button({
  variant = "primario",
  size = "md",
  cargando = false,
  iconoIzquierda: IconoIzquierda,
  iconoDerecha: IconoDerecha,
  className = "",
  children,
  disabled,
  ...props
}) {
  return (
    <button
      disabled={disabled || cargando}
      aria-busy={cargando || undefined}
      className={`inline-flex items-center justify-center rounded-lg etiqueta font-medium
        transition-all duration-150 disabled:cursor-not-allowed
        ${VARIANTES[variant] ?? VARIANTES.primario} ${TAMANOS[size] ?? TAMANOS.md} ${className}`}
      {...props}
    >
      {cargando ? (
        <Loader2 size={14} className="animate-spin" aria-hidden="true" />
      ) : (
        IconoIzquierda && <IconoIzquierda size={14} aria-hidden="true" />
      )}
      {children}
      {!cargando && IconoDerecha && <IconoDerecha size={14} aria-hidden="true" />}
    </button>
  );
}

export default Button;
