function QuienesSomos() {
  const cards = [
    {
      title: "Nuestra misión",
      text: "Acercar el arte original a nuevos coleccionistas, con precios justos tanto para quien compra como para quien crea.",
    },
    {
      title: "Nuestros artistas",
      text: "Trabajamos con un grupo curado de pintores colombianos que exploran técnicas de óleo y acrílico sobre lienzo.",
    },
    {
      title: "Cómo trabajamos",
      text: "Cada obra se autentica, se fotografía en alta resolución y se envía con certificado de originalidad a cualquier ciudad del país.",
    },
  ];

  return (
    <div className="container mx-auto max-w-4xl px-6 py-14 sm:py-20">
      <span className="font-mono text-xs uppercase tracking-widest text-sienna">
        Desde 2015
      </span>
      <h1 className="font-display text-3xl sm:text-4xl mt-2 mb-5">
        Quiénes Somos
      </h1>
      <p className="text-ink/80 max-w-2xl leading-relaxed mb-10 text-sm sm:text-base">
        Óleo &amp; Lienzo nació como un espacio pequeño en el que cuatro
        artistas independientes decidieron compartir estudio. Hoy somos una
        galería que representa a creadores emergentes y consolidados,
        acompañándolos desde el primer boceto hasta la venta de cada pieza.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {cards.map((c) => (
          <article
            key={c.title}
            className="bg-paper border-t-4 border-gold rounded-xl p-6 shadow-sm"
          >
            <h3 className="font-display text-lg mb-2">{c.title}</h3>
            <p className="text-sm text-ink/75 leading-relaxed">{c.text}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

export default QuienesSomos;
