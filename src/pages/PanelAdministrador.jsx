import { useState } from "react";
import {
  Activity, BarChart3, Brush, FileText, MessageSquareWarning,
  Package, ShoppingCart, Users,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import PanelLayout from "./PanelLayout";
import DashboardPanel from "./panel/DashboardPanel";
import Diagnostico from "./panel/Diagnostico";
import FacturasManager from "./panel/FacturasManager";
import ObrasManager from "./panel/ObrasManager";
import PedidosManager from "./panel/PedidosManager";
import PqrManager from "./panel/PqrManager";
import ReportesPanel from "./panel/ReportesPanel";
import ServiciosManager from "./panel/ServiciosManager";
import UsuariosManager from "./panel/UsuariosManager";
import VentasManager from "./panel/VentasManager";

const PESTANAS = [
  { id: "dashboard", label: "Dashboard", icono: BarChart3 },
  { id: "ventas", label: "Ventas", icono: ShoppingCart },
  { id: "facturas", label: "Facturas", icono: FileText },
  { id: "reportes", label: "Reportes", icono: FileText },
  { id: "pedidos", label: "Pedidos", icono: Package },
  { id: "obras", label: "Obras", icono: Brush },
  { id: "servicios", label: "Servicios", icono: Package },
  { id: "pqr", label: "PQR", icono: MessageSquareWarning },
  { id: "usuarios", label: "Usuarios", icono: Users },
  { id: "diagnostico", label: "Diagnóstico", icono: Activity },
];

/** Panel del administrador: acceso completo a todos los módulos. */
function PanelAdministrador() {
  const { token } = useAuth();
  const [pestana, setPestana] = useState("dashboard");

  const vistas = {
    dashboard: <DashboardPanel token={token} />,
    ventas: <VentasManager token={token} />,
    facturas: <FacturasManager token={token} puedeGestionar />,
    reportes: <ReportesPanel token={token} />,
    pedidos: <PedidosManager token={token} />,
    obras: <ObrasManager token={token} puedeEliminar />,
    servicios: <ServiciosManager token={token} puedeEliminar />,
    pqr: <PqrManager token={token} puedeGestionar />,
    usuarios: <UsuariosManager token={token} />,
    diagnostico: <Diagnostico token={token} />,
  };

  return (
    <PanelLayout
      titulo="Administración de la galería"
      descripcion="Control total: catálogo, ventas, facturación, usuarios y estado del sistema."
      pestanas={PESTANAS}
      activa={pestana}
      onCambiar={setPestana}
    >
      {vistas[pestana]}
    </PanelLayout>
  );
}

export default PanelAdministrador;
