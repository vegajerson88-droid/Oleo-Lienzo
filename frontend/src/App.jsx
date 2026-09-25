import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import MainLayout from "./components/MainLayout";
import RequireRole from "./components/RequireRole";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import Catalogo from "./pages/Catalogo";
import Contacto from "./pages/Contacto";
import Index from "./pages/Index";
import Login from "./pages/Login";
import NoEncontrado from "./pages/NoEncontrado";
import PanelAdministrador from "./pages/PanelAdministrador";
import PanelCliente from "./pages/PanelCliente";
import PanelEmpleado from "./pages/PanelEmpleado";
import QuienesSomos from "./pages/QuienesSomos";
import RestablecerPassword from "./pages/RestablecerPassword";

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Páginas con cabecera, pie, WhatsApp y chatbot */}
            <Route element={<MainLayout />}>
              <Route path="/" element={<Index />} />
              <Route path="/catalogo" element={<Catalogo />} />
              <Route path="/quienes-somos" element={<QuienesSomos />} />
              <Route path="/contacto" element={<Contacto />} />

              {/* Paneles protegidos por rol */}
              <Route
                path="/panel/cliente"
                element={
                  <RequireRole roles={["cliente"]}>
                    <PanelCliente />
                  </RequireRole>
                }
              />
              <Route
                path="/panel/empleado"
                element={
                  <RequireRole roles={["empleado"]}>
                    <PanelEmpleado />
                  </RequireRole>
                }
              />
              <Route
                path="/panel/administrador"
                element={
                  <RequireRole roles={["administrador"]}>
                    <PanelAdministrador />
                  </RequireRole>
                }
              />

              <Route path="*" element={<NoEncontrado />} />
            </Route>

            {/* Páginas a pantalla completa, sin la estructura del sitio */}
            <Route path="/login" element={<Login />} />
            <Route path="/restablecer" element={<RestablecerPassword />} />
            <Route path="/registro" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
