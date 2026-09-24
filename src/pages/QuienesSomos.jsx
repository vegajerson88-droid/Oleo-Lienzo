import { Award, Heart, Users } from "lucide-react";

const VALORES = [
  {
    Icono: Heart,
    titulo: "Nuestra misión",
    texto:
      "Acercar el arte original a nuevos coleccionistas, con precios justos tanto " +
      "para quien compra como para quien crea.",
  },
  {
    Icono: Users,
    titulo: "Nuestros artistas",
    texto:
      "Trabajamos con un grupo curado de pintores colombianos que exploran técnicas " +
      "de óleo y acrílico sobre lienzo.",
  },
  {
    Icono: Award,
    titulo: "Cómo trabajamos",
    texto:
      "Cada obra se autentica, se fotografía en alta resolución y se envía con " +
      "certificado de originalidad a cualquier ciudad del país.",
  },
];

const HITOS = [
  { anio: "2015", titulo: "Un estudio compartido",
    texto: "Cuatro artistas independientes deciden compartir espacio y gastos en el centro de Bogotá." },
  { anio: "2018", titulo: "La primera exposición colectiva",
    texto: "El estudio abre sus puertas al público y vende sus primeras piezas a coleccionistas." },
  { anio: "2021", titulo: "Galería y representación",
    texto: "Empezamos a representar formalmente a los artistas y a gestionar sus ventas." },
  { anio: "Hoy", titulo: "Catálogo en línea",
    texto: "La colección se puede recorrer, pedir y facturar desde cualquier lugar." },
];

function QuienesSomos() {
  return (
    <div>
      <section className="border-b border-line bg-paper">
        <div className="contenedor max-w-4xl py-14 sm:py-20">
          <span className="etiqueta text-sienna">Desde 2015</span>
          <h1 className="mb-5 mt-2 font-display text-3xl sm:text-4xl">Quiénes Somos</h1>
          <p className="max-w-2xl text-sm leading-relaxed text-ink-soft sm:text-base">
            Óleo &amp; Lienzo nació como un espacio pequeño en el que cuatro artistas
            independientes decidieron compartir estudio. Hoy somos una galería que
            representa a creadores emergentes y consolidados, acompañándolos desde
            el primer boceto hasta la venta de cada pieza.
          </p>
        </div>
      </section>

      <section className="contenedor max-w-5xl py-14">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {VALORES.map(({ Icono, titulo, texto }) => (
            <article key={titulo} className="rounded-xl border-t-4 border-gold bg-paper p-6 shadow-suave">
              <Icono size={24} className="mb-3 text-forest" aria-hidden="true" />
              <h2 className="mb-2 font-display text-lg">{titulo}</h2>
              <p className="text-sm leading-relaxed text-ink-soft">{texto}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="contenedor max-w-3xl pb-16 sm:pb-20">
        <h2 className="mb-8 text-center font-display text-2xl">Nuestra trayectoria</h2>
        <ol className="relative border-l-2 border-gold/30 pl-8">
          {HITOS.map(({ anio, titulo, texto }) => (
            <li key={anio} className="relative mb-9 last:mb-0">
              <span
                className="absolute -left-[41px] flex h-5 w-5 items-center justify-center
                           rounded-full border-2 border-gold bg-paper"
                aria-hidden="true"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-gold" />
              </span>
              <span className="etiqueta text-gold">{anio}</span>
              <h3 className="mt-1 font-display text-lg">{titulo}</h3>
              <p className="mt-1 text-sm leading-relaxed text-ink-soft">{texto}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

export default QuienesSomos;
