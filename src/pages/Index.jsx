import { Link } from "react-router-dom";
import { Palette, Truck, ShieldCheck } from "lucide-react";
import Carousel from "../components/Carousel";

const features = [
  {
    Icon: Palette,
    title: "Piezas 100% originales",
    text: "Cada obra es única, firmada y autenticada directamente por su artista.",
  },
  {
    Icon: Truck,
    title: "Envíos a todo el país",
    text: "Empacamos con materiales especializados para proteger cada lienzo en tránsito.",
  },
  {
    Icon: ShieldCheck,
    title: "Certificado de autenticidad",
    text: "Recibe tu obra con documento de respaldo y garantía de originalidad.",
  },
];

function Index() {
  return (
    <div>
      <section className="bg-gradient-to-b from-forest to-forest-dark text-paper">
        <div className="container mx-auto max-w-6xl px-6 py-16 sm:py-20 text-center">
          <span className="font-mono text-xs uppercase tracking-widest text-gold">
            Colección permanente
          </span>
          <h1 className="font-display text-3xl sm:text-5xl mt-3 mb-5 max-w-3xl mx-auto">
            Diez lienzos, diez maneras de mirar el mundo
          </h1>
          <p className="text-paper/80 max-w-xl mx-auto mb-8 text-sm sm:text-base">
            Recorre nuestra selección curada de piezas originales. Cada obra
            incluye su ficha técnica y está disponible para adquisición
            directa con el artista.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <a
              href="#coleccion"
              className="font-mono text-xs uppercase tracking-wider bg-gold text-forest-dark px-6 py-3 rounded-md hover:bg-gold/90 transition-colors"
            >
              Ver colección
            </a>
            <Link
              to="/contacto"
              className="font-mono text-xs uppercase tracking-wider border border-paper/40 text-paper px-6 py-3 rounded-md hover:border-gold hover:text-gold transition-colors"
            >
              Contáctanos
            </Link>
          </div>
        </div>
      </section>

      <section id="coleccion" className="py-14 sm:py-20 -mt-1">
        <Carousel />
      </section>

      <section className="container mx-auto max-w-6xl px-6 pb-16 sm:pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {features.map(({ Icon, title, text }) => (
            <div
              key={title}
              className="bg-paper rounded-xl border-t-4 border-gold p-6 shadow-sm"
            >
              <Icon className="text-forest mb-3" size={26} />
              <h3 className="font-display text-lg mb-1.5">{title}</h3>
              <p className="text-sm text-ink/75">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-paper border-y border-ink/10">
        <div className="container mx-auto max-w-4xl px-6 py-14 text-center">
          <h2 className="font-display text-2xl sm:text-3xl mb-3">
            Únete a nuestra comunidad de coleccionistas
          </h2>
          <p className="text-ink/75 max-w-xl mx-auto mb-7 text-sm sm:text-base">
            Crea una cuenta para guardar tus piezas favoritas, recibir
            novedades de la galería y agilizar tu próxima compra.
          </p>
          <Link
            to="/login"
            className="inline-block font-mono text-xs uppercase tracking-wider bg-forest text-paper px-7 py-3 rounded-md hover:bg-forest-dark transition-colors"
          >
            Crear cuenta / Iniciar sesión
          </Link>
        </div>
      </section>
    </div>
  );
}

export default Index;
