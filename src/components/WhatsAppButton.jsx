import { MessageCircle } from "lucide-react";

// Número de contacto de la galería. Ajustar al número real del negocio.
const WHATSAPP_NUMERO = "573000000000";
const MENSAJE_DEFECTO = "Hola, quiero más información sobre Óleo & Lienzo.";

function WhatsAppButton() {
  const href = `https://wa.me/${WHATSAPP_NUMERO}?text=${encodeURIComponent(MENSAJE_DEFECTO)}`;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Escribir por WhatsApp"
      className="fixed bottom-5 right-5 z-40 flex items-center justify-center w-14 h-14 rounded-full bg-[#25D366] text-white shadow-lg shadow-ink/20 hover:scale-105 transition-transform"
    >
      <MessageCircle size={28} fill="white" strokeWidth={0} />
    </a>
  );
}

export default WhatsAppButton;
