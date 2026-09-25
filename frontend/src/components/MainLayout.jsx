import { Outlet } from "react-router-dom";

import ChatbotWidget from "./ChatbotWidget";
import Footer from "./Footer";
import Header from "./Header";
import WhatsAppButton from "./WhatsAppButton";

function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Salto de navegación para quien usa teclado o lector de pantalla. */}
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50
                   focus:rounded-lg focus:bg-forest focus:px-4 focus:py-2 focus:text-paper"
      >
        Saltar al contenido
      </a>

      <Header />
      {/* `pb-28` deja hueco a los botones flotantes de WhatsApp y del chatbot,
          que en móvil se superpondrían al contenido del final de la página. */}
      <main id="contenido" className="flex-1 pb-28 sm:pb-0">
        <Outlet />
      </main>
      <Footer />

      <WhatsAppButton />
      <ChatbotWidget />
    </div>
  );
}

export default MainLayout;
