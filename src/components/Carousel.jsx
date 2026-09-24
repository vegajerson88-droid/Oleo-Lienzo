import { useState, useCallback, useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import artData from "../data/artData";

function Carousel() {
  const [current, setCurrent] = useState(0);
  const total = artData.length;

  const goNext = useCallback(() => {
    setCurrent((prev) => (prev + 1) % total);
  }, [total]);

  const goPrev = useCallback(() => {
    setCurrent((prev) => (prev - 1 + total) % total);
  }, [total]);

  useEffect(() => {
    const timer = setInterval(goNext, 6000);
    return () => clearInterval(timer);
  }, [goNext]);

  const piece = artData[current];
  const catalogNumber = String(piece.id).padStart(3, "0");

  return (
    <section
      className="max-w-4xl mx-auto px-4 sm:px-6"
      aria-roledescription="carrusel"
      aria-label="Pinturas destacadas"
    >
      <div className="flex flex-col md:flex-row gap-6 md:gap-10 items-center md:items-stretch bg-paper rounded-2xl shadow-xl shadow-ink/10 border border-ink/5 p-4 sm:p-6">
        <div className="relative w-full md:w-1/2 flex-shrink-0">
          <div className="relative overflow-hidden rounded-xl ring-1 ring-gold/50 shadow-md">
            <img
              src={piece.image}
              alt={`${piece.title}, de ${piece.artist}`}
              className="w-full aspect-4/5 object-cover transition-opacity duration-500"
            />
          </div>

          <button
            onClick={goPrev}
            aria-label="Pintura anterior"
            className="absolute top-1/2 -translate-y-1/2 -left-3 sm:-left-4 w-10 h-10 rounded-full bg-white/90 backdrop-blur border border-ink/10 text-forest shadow-md flex items-center justify-center hover:bg-forest hover:text-paper transition-colors"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            onClick={goNext}
            aria-label="Siguiente pintura"
            className="absolute top-1/2 -translate-y-1/2 -right-3 sm:-right-4 w-10 h-10 rounded-full bg-white/90 backdrop-blur border border-ink/10 text-forest shadow-md flex items-center justify-center hover:bg-forest hover:text-paper transition-colors"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        <div className="w-full md:w-1/2 flex flex-col justify-center border-t md:border-t-0 md:border-l border-gold/40 pt-5 md:pt-0 md:pl-8">
          <span className="font-mono text-xs uppercase tracking-widest text-sienna">
            Cat. N.º {catalogNumber}
          </span>
          <h3 className="font-display italic text-2xl sm:text-3xl mt-2 mb-1">
            {piece.title}
          </h3>
          <p className="text-sm text-ink/80">
            {piece.artist}, {piece.year}
          </p>
          <p className="font-mono text-[11px] uppercase tracking-wide text-ink/50 mb-4">
            {piece.technique}
          </p>
          <p className="text-sm leading-relaxed text-ink/85 mb-5">
            {piece.description}
          </p>
          <span className="font-mono font-bold text-lg text-forest">
            {piece.price}
          </span>
        </div>
      </div>

      <div className="flex justify-center gap-2 mt-6">
        {artData.map((item, index) => (
          <button
            key={item.id}
            onClick={() => setCurrent(index)}
            aria-label={`Ir a la pintura ${index + 1}: ${item.title}`}
            className={`h-2.5 rounded-full transition-all ${
              index === current ? "w-6 bg-gold" : "w-2.5 bg-forest/30 hover:bg-forest/50"
            }`}
          />
        ))}
      </div>
    </section>
  );
}

export default Carousel;
