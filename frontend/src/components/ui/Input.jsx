import { useId, useState } from "react";
import { AlertCircle, Check, Eye, EyeOff } from "lucide-react";

/**
 * Campo de texto con etiqueta, validación visual y contador de caracteres.
 *
 * Muestra el error en rojo y, cuando el campo ya se tocó y es válido, una
 * marca verde: el usuario sabe que va bien sin tener que enviar el formulario.
 */
function Input({
  label,
  name,
  error,
  hint,
  valido = false,
  type = "text",
  className = "",
  contador = false,
  maxLength,
  value,
  ...props
}) {
  const [verPassword, setVerPassword] = useState(false);
  const idGenerado = useId();
  const id = props.id || `${name || "campo"}-${idGenerado}`;

  const esPassword = type === "password";
  const tipoReal = esPassword ? (verPassword ? "text" : "password") : type;
  const hayError = Boolean(error);

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="etiqueta text-ink-soft font-medium">
          {label}
          {props.required && <span className="text-sienna ml-0.5">*</span>}
        </label>
      )}

      <div className="relative flex items-center">
        <input
          id={id}
          name={name}
          type={tipoReal}
          value={value}
          maxLength={maxLength}
          aria-invalid={hayError || undefined}
          aria-describedby={hayError ? `${id}-error` : hint ? `${id}-ayuda` : undefined}
          className={`w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-ink
            placeholder:text-muted/60 transition-colors
            focus:outline-none focus:ring-2 focus:ring-gold/50 focus:border-gold
            disabled:bg-paper-dim disabled:text-muted disabled:cursor-not-allowed
            ${esPassword || valido ? "pr-10" : ""}
            ${hayError ? "border-error bg-error-suave/40" : "border-line"}
            ${className}`}
          {...props}
        />

        {esPassword && (
          <button
            type="button"
            onClick={() => setVerPassword((v) => !v)}
            aria-label={verPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            tabIndex={-1}
            className="absolute right-3 text-muted hover:text-forest transition-colors"
          >
            {verPassword ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        )}

        {!esPassword && valido && !hayError && (
          <Check size={17} className="absolute right-3 text-exito" aria-hidden="true" />
        )}
      </div>

      <div className="flex items-start justify-between gap-3 min-h-[16px]">
        {hayError ? (
          <span id={`${id}-error`} role="alert" className="flex items-center gap-1 text-xs text-error">
            <AlertCircle size={12} className="shrink-0" aria-hidden="true" />
            {error}
          </span>
        ) : hint ? (
          <span id={`${id}-ayuda`} className="text-xs text-muted">
            {hint}
          </span>
        ) : (
          <span />
        )}

        {contador && maxLength && (
          <span className="font-mono text-[10px] text-muted shrink-0 tabular-nums">
            {(value ?? "").length}/{maxLength}
          </span>
        )}
      </div>
    </div>
  );
}

export default Input;
