import { useId } from "react";
import { AlertCircle, ChevronDown } from "lucide-react";

function Select({ label, name, error, hint, options = [], className = "", ...props }) {
  const idGenerado = useId();
  const id = props.id || `${name || "seleccion"}-${idGenerado}`;
  const hayError = Boolean(error);

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="etiqueta text-ink-soft font-medium">
          {label}
          {props.required && <span className="text-sienna ml-0.5">*</span>}
        </label>
      )}

      <div className="relative">
        <select
          id={id}
          name={name}
          aria-invalid={hayError || undefined}
          aria-describedby={hayError ? `${id}-error` : undefined}
          className={`w-full appearance-none rounded-lg border bg-white px-3.5 py-2.5 pr-10
            text-sm text-ink transition-colors cursor-pointer
            focus:outline-none focus:ring-2 focus:ring-gold/50 focus:border-gold
            disabled:bg-paper-dim disabled:text-muted disabled:cursor-not-allowed
            ${hayError ? "border-error bg-error-suave/40" : "border-line"}
            ${className}`}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown
          size={16}
          className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted"
          aria-hidden="true"
        />
      </div>

      <div className="min-h-[16px]">
        {hayError ? (
          <span id={`${id}-error`} role="alert" className="flex items-center gap-1 text-xs text-error">
            <AlertCircle size={12} className="shrink-0" aria-hidden="true" />
            {error}
          </span>
        ) : hint ? (
          <span className="text-xs text-muted">{hint}</span>
        ) : null}
      </div>
    </div>
  );
}

export default Select;
