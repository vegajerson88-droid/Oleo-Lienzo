/** Monograma e identidad de la galería, reutilizado en cabecera, login y pie. */
function Logo({ tamano = "md", invertido = true, className = "" }) {
  const medidas = {
    sm: { circulo: "h-8 w-8 text-base", texto: "text-lg" },
    md: { circulo: "h-9 w-9 text-lg", texto: "text-xl" },
    lg: { circulo: "h-14 w-14 text-2xl", texto: "text-3xl" },
  }[tamano];

  return (
    <span className={`flex items-center gap-3 ${className}`}>
      <span
        className={`flex shrink-0 items-center justify-center rounded-full border-2 border-gold
          font-display italic text-gold ${medidas.circulo}`}
        aria-hidden="true"
      >
        O
      </span>
      <span
        className={`font-display whitespace-nowrap ${medidas.texto}
          ${invertido ? "text-paper" : "text-forest"}`}
      >
        Óleo<span className="px-0.5 italic text-gold">&amp;</span>Lienzo
      </span>
    </span>
  );
}

export default Logo;
