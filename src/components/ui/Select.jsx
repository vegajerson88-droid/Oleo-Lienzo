function Select({ label, name, error, options = [], className = "", ...props }) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && (
        <span className="font-mono text-xs uppercase tracking-wider text-ink/80">
          {label}
        </span>
      )}
      <select
        name={name}
        className={`rounded-md border px-3 py-2.5 text-sm text-ink bg-white transition-colors
          focus:outline-none focus:ring-2 focus:ring-gold/60
          ${error ? "border-sienna" : "border-ink/20"}
          ${className}`}
        aria-invalid={!!error}
        aria-describedby={error ? `${name}-error` : undefined}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && (
        <span id={`${name}-error`} className="text-xs text-sienna">
          {error}
        </span>
      )}
    </label>
  );
}

export default Select;
