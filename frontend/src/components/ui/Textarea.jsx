import { useId } from "react";
import { AlertCircle } from "lucide-react";

function Textarea({
  label, name, error, hint, className = "", contador = false, maxLength, value, rows = 4, ...props
}) {
  const idGenerado = useId();
  const id = props.id || `${name || "texto"}-${idGenerado}`;
  const hayError = Boolean(error);

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="etiqueta text-ink-soft font-medium">
          {label}
          {props.required && <span className="text-sienna ml-0.5">*</span>}
        </label>
      )}

      <textarea
        id={id}
        name={name}
        rows={rows}
        value={value}
        maxLength={maxLength}
        aria-invalid={hayError || undefined}
        aria-describedby={hayError ? `${id}-error` : undefined}
        className={`w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-ink resize-y
          placeholder:text-muted/60 transition-colors
          focus:outline-none focus:ring-2 focus:ring-gold/50 focus:border-gold
          disabled:bg-paper-dim disabled:text-muted
          ${hayError ? "border-error bg-error-suave/40" : "border-line"} ${className}`}
        {...props}
      />

      <div className="flex items-start justify-between gap-3 min-h-[16px]">
        {hayError ? (
          <span id={`${id}-error`} role="alert" className="flex items-center gap-1 text-xs text-error">
            <AlertCircle size={12} className="shrink-0" aria-hidden="true" />
            {error}
          </span>
        ) : hint ? (
          <span className="text-xs text-muted">{hint}</span>
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

export default Textarea;
