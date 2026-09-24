const VARIANTS = {
  primary:
    "bg-forest text-paper hover:bg-forest-dark disabled:opacity-50 disabled:cursor-not-allowed",
  outline:
    "border border-forest text-forest hover:bg-forest hover:text-paper disabled:opacity-50",
  ghost: "text-forest hover:bg-forest/10 disabled:opacity-50",
};

function Button({ variant = "primary", className = "", children, ...props }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-md px-5 py-2.5
        font-mono text-xs uppercase tracking-wider transition-colors
        ${VARIANTS[variant] || VARIANTS.primary} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export default Button;
