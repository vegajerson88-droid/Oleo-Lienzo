import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

function Input({ label, name, error, hint, type = "text", className = "", ...props }) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === "password";
  const resolvedType = isPassword ? (showPassword ? "text" : "password") : type;

  return (
    <label className="flex flex-col gap-1.5">
      {label && (
        <span className="font-mono text-xs uppercase tracking-wider text-ink/80">
          {label}
        </span>
      )}
      <span className="relative flex items-center">
        <input
          name={name}
          type={resolvedType}
          className={`w-full rounded-md border px-3 py-2.5 text-sm text-ink bg-white transition-colors
            focus:outline-none focus:ring-2 focus:ring-gold/60
            ${isPassword ? "pr-10" : ""}
            ${error ? "border-sienna" : "border-ink/20"}
            ${className}`}
          aria-invalid={!!error}
          aria-describedby={error ? `${name}-error` : undefined}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            aria-pressed={showPassword}
            tabIndex={-1}
            className="absolute right-2.5 text-ink/50 hover:text-forest transition-colors"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </span>
      {error ? (
        <span id={`${name}-error`} className="text-xs text-sienna">
          {error}
        </span>
      ) : hint ? (
        <span className="text-xs text-ink/50">{hint}</span>
      ) : null}
    </label>
  );
}

export default Input;
