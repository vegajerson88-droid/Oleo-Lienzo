import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import MainLayout from "./components/MainLayout";
import RequireRole from "./components/RequireRole";
import Index from "./pages/Index";
import QuienesSomos from "./pages/QuienesSomos";
import Contacto from "./pages/Contacto";
import Login from "./pages/Login";
import PanelCliente from "./pages/PanelCliente";
import PanelEmpleado from "./pages/PanelEmpleado";
import PanelAdministrador from "./pages/PanelAdministrador";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Index />} />
            <Route path="/quienes-somos" element={<QuienesSomos />} />
            <Route path="/contacto" element={<Contacto />} />
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
                <RequireRole roles={["empleado", "administrador"]}>
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
          </Route>

          {/* El login no usa el layout: no muestra Header ni Footer */}
          <Route path="/login" element={<Login />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
