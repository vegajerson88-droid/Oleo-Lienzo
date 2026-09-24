import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";

import artData from "../data/artData";

const INTERVALO = 6000;

/**
 * Carrusel de las diez obras destacadas de la galería.
 *
 * Avanza solo, pero se detiene al pasar el ratón o al enfocar con el teclado,
 * y ofrece un control explícito de pausa: un carrusel que no se puede parar
 * es una barrera de accesibilidad.
 */
function Carousel() {
  const [actual, setActual] = useState(0);
  const [pausado, setPausado] = useState(false);
  const total = artData.length;
  const regionRef = useRef(null);

  const siguiente = useCallback(() => setActual((i) => (i + 1) % total), [total]);
  const anterior = useCallback(() => setActual((i) => (i - 1 + total) % total), [total]);

  useEffect(() => {
    if (pausado) return;
    const temporizador = setInterval(siguiente, INTERVALO);
    return () => clearInterval(temporizador);
  }, [siguiente, pausado]);

  // Flechas del teclado cuando el carrusel tiene el foco.
  useEffect(() => {
    const region = regionRef.current;
    if (!region) return;
    const alPulsar = (evento) => {
      if (evento.key === "ArrowRight") siguiente();
      if (evento.key === "ArrowLeft") anterior();
    };
    region.addEventListener("keydown", alPulsar);
    return () => region.removeEventListener("keydown", alPulsar);
  }, [siguiente, anterior]);

  const obra = artData[actual];
  const numeroCatalogo = String(obra.id).padStart(3, "0");

  return (
    <section
      ref={regionRef}
      tabIndex={-1}
      aria-roledescription="carrusel"
      aria-label="Obras destacadas de la colección"
      className="contenedor max-w-5xl"
      onMouseEnter={() => setPausado(true)}
      onMouseLeave={() => setPausado(false)}
      onFocusCapture={() => setPausado(true)}
      onBlurCapture={() => setPausado(false)}
    >
      <div className="grid grid-cols-1 gap-6 rounded-2xl border border-line/70 bg-paper p-4
                      shadow-media sm:p-6 md:grid-cols-2 md:gap-10">
        {/* Obra */}
        <div className="relative">
          <div className="overflow-hidden rounded-xl shadow-media ring-1 ring-gold/40">
            <img
              key={obra.id}
              src={obra.image}
              alt={`${obra.title}, de ${obra.artist}`}
              loading="lazy"
              className="aspect-4/5 w-full object-cover animate-aparecer"
            />
          </div>

          <button
            type="button"
            onClick={anterior}
            aria-label="Obra anterior"
            className="absolute -left-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center
                       justify-center rounded-full border border-line bg-paper/95 text-forest
                       shadow-media backdrop-blur transition-colors
                       hover:bg-forest hover:text-paper sm:-left-4"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            type="button"
            onClick={siguiente}
            aria-label="Obra siguiente"
            className="absolute -right-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center
                       justify-center rounded-full border border-line bg-paper/95 text-forest
                       shadow-media backdrop-blur transition-colors
                       hover:bg-forest hover:text-paper sm:-right-4"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Ficha técnica */}
        <div
          className="flex flex-col justify-center border-t border-gold/40 pt-5
                     md:border-l md:border-t-0 md:pl-8 md:pt-0"
          aria-live="polite"
          aria-atomic="true"
        >
          <span className="etiqueta text-sienna">Cat. N.º {numeroCatalogo}</span>
          <h3 className="mb-1 mt-2 font-display text-2xl italic sm:text-3xl">{obra.title}</h3>
          <p className="text-sm text-ink-soft">
            {obra.artist}, {obra.year}
          </p>
          <p className="mb-4 etiqueta text-muted">{obra.technique}</p>
          <p className="mb-5 text-sm leading-relaxed text-ink-soft">{obra.description}</p>
          <span className="font-mono text-lg font-bold tabular-nums text-forest">
            {obra.price}
          </span>
        </div>
      </div>

      {/* Indicadores y pausa */}
      <div className="mt-6 flex items-center justify-center gap-3">
        <button
          type="button"
          onClick={() => setPausado((p) => !p)}
          aria-label={pausado ? "Reanudar el carrusel" : "Pausar el carrusel"}
          className="flex h-7 w-7 items-center justify-center rounded-full border border-line
                     text-muted transition-colors hover:border-forest hover:text-forest"
        >
          {pausado ? <Play size={12} /> : <Pause size={12} />}
        </button>

        <div className="flex flex-wrap justify-center gap-2">
          {artData.map((pieza, indice) => (
            <button
              key={pieza.id}
              type="button"
              onClick={() => setActual(indice)}
              aria-label={`Ver la obra ${indice + 1}: ${pieza.title}`}
              aria-current={indice === actual}
              className={`h-2.5 rounded-full transition-all ${
                indice === actual ? "w-7 bg-gold" : "w-2.5 bg-forest/25 hover:bg-forest/45"
              }`}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export default Carousel;
