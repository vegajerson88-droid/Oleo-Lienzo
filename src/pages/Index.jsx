import { Link } from "react-router-dom";
import { ArrowRight, Palette, ShieldCheck, Sparkles, Truck } from "lucide-react";

import Carousel from "../components/Carousel";

const GARANTIAS = [
  {
    Icono: Palette,
    titulo: "Piezas 100% originales",
    texto: "Cada obra es única, firmada y autenticada directamente por su artista.",
  },
  {
    Icono: Truck,
    titulo: "Envíos a todo el país",
    texto: "Empacamos con materiales especializados para proteger cada lienzo en tránsito.",
  },
  {
    Icono: ShieldCheck,
    titulo: "Certificado de autenticidad",
    texto: "Recibe tu obra con documento de respaldo y garantía de originalidad.",
  },
];

const CIFRAS = [
  { valor: "10", etiqueta: "Obras en colección" },
  { valor: "4", etiqueta: "Artistas representados" },
  { valor: "2015", etiqueta: "Desde" },
  { valor: "100%", etiqueta: "Piezas originales" },
];

function Index() {
  return (
    <div>
      {/* Portada */}
      <section className="relative overflow-hidden bg-gradient-to-b from-forest to-forest-dark text-paper">
        {/* Textura sutil de fondo, puramente decorativa. */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          aria-hidden="true"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 30%, #c9a227 0%, transparent 42%), " +
              "radial-gradient(circle at 80% 70%, #c9a227 0%, transparent 42%)",
          }}
        />

        <div className="contenedor relative py-16 text-center sm:py-24">
          <span className="inline-flex items-center gap-2 rounded-full border border-gold/40
                           bg-gold/10 px-4 py-1.5 etiqueta text-gold">
            <Sparkles size={12} aria-hidden="true" />
            Colección permanente
          </span>

          <h1 className="mx-auto mt-5 max-w-3xl font-display text-3xl leading-tight sm:text-5xl">
            Diez lienzos, diez maneras de mirar el mundo
          </h1>

          <p className="mx-auto mb-9 mt-5 max-w-xl text-sm text-paper/80 sm:text-base">
            Recorre nuestra selección curada de piezas originales. Cada obra incluye
            su ficha técnica y está disponible para adquisición directa con el artista.
          </p>

          <div className="flex flex-wrap justify-center gap-3">
            <Link
              to="/catalogo"
              className="inline-flex items-center gap-2 rounded-lg bg-gold px-6 py-3.5 etiqueta
                         font-semibold text-forest-dark transition-colors hover:bg-gold-soft"
            >
              Ver el catálogo
              <ArrowRight size={14} aria-hidden="true" />
            </Link>
            <Link
              to="/contacto"
              className="inline-flex items-center gap-2 rounded-lg border border-paper/35 px-6 py-3.5
                         etiqueta text-paper transition-colors hover:border-gold hover:text-gold"
            >
              Contáctanos
            </Link>
          </div>

          {/* Cifras de la galería */}
          <dl className="mx-auto mt-14 grid max-w-2xl grid-cols-2 gap-6 border-t border-paper/15
                         pt-9 sm:grid-cols-4">
            {CIFRAS.map(({ valor, etiqueta }) => (
              <div key={etiqueta}>
                <dt className="sr-only">{etiqueta}</dt>
                <dd>
                  <span className="block font-display text-2xl text-gold sm:text-3xl">{valor}</span>
                  <span className="mt-1 block etiqueta text-paper/60">{etiqueta}</span>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Carrusel */}
      <section id="coleccion" className="py-14 sm:py-20">
        <div className="contenedor mb-8 text-center">
          <span className="etiqueta text-sienna">Obras destacadas</span>
          <h2 className="mt-2 font-display text-2xl sm:text-3xl">
            Recorre la colección pieza a pieza
          </h2>
        </div>
        <Carousel />
      </section>

      {/* Garantías */}
      <section className="contenedor pb-16 sm:pb-20">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {GARANTIAS.map(({ Icono, titulo, texto }) => (
            <article
              key={titulo}
              className="rounded-xl border-t-4 border-gold bg-paper p-6 shadow-suave
                         transition-shadow hover:shadow-media"
            >
              <Icono className="mb-3 text-forest" size={26} aria-hidden="true" />
              <h3 className="mb-1.5 font-display text-lg">{titulo}</h3>
              <p className="text-sm leading-relaxed text-ink-soft">{texto}</p>
            </article>
          ))}
        </div>
      </section>

      {/* Llamada a la acción */}
      <section className="border-y border-line bg-paper">
        <div className="contenedor max-w-3xl py-14 text-center">
          <h2 className="mb-3 font-display text-2xl sm:text-3xl">
            Únete a nuestra comunidad de coleccionistas
          </h2>
          <p className="mx-auto mb-7 max-w-xl text-sm text-ink-soft sm:text-base">
            Crea una cuenta para hacer pedidos, consultar tus facturas y recibir
            novedades de la galería.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-lg bg-forest px-7 py-3.5 etiqueta
                       text-paper transition-colors hover:bg-forest-dark"
          >
            Crear cuenta o iniciar sesión
            <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </div>
      </section>
    </div>
  );
}

export default Index;
