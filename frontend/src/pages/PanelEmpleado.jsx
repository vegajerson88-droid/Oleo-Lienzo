import { useState } from "react";
import { BarChart3, Brush, FileText, MessageSquareWarning, Package, ShoppingCart } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import PanelLayout from "./PanelLayout";
import DashboardPanel from "./panel/DashboardPanel";
import FacturasManager from "./panel/FacturasManager";
import ObrasManager from "./panel/ObrasManager";
import PedidosManager from "./panel/PedidosManager";
import PqrManager from "./panel/PqrManager";
import ReportesPanel from "./panel/ReportesPanel";
import ServiciosManager from "./panel/ServiciosManager";
import VentasManager from "./panel/VentasManager";

const PESTANAS = [
  { id: "dashboard", label: "Dashboard", icono: BarChart3 },
  { id: "pedidos", label: "Pedidos", icono: Package },
  { id: "ventas", label: "Ventas", icono: ShoppingCart },
  { id: "facturas", label: "Facturas", icono: FileText },
  { id: "reportes", label: "Reportes", icono: FileText },
  { id: "obras", label: "Obras", icono: Brush },
  { id: "servicios", label: "Servicios", icono: Package },
  { id: "pqr", label: "PQR", icono: MessageSquareWarning },
];

/**
 * Panel del empleado.
 *
 * Tiene lo operativo —catálogo, pedidos, ventas, facturas y PQR— pero no
 * gestiona usuarios, no elimina del catálogo y su dashboard no incluye
 * ingresos globales. Esas restricciones también las impone el backend.
 */
function PanelEmpleado() {
  const { token } = useAuth();
  const [pestana, setPestana] = useState("dashboard");

  const vistas = {
    dashboard: <DashboardPanel token={token} />,
    pedidos: <PedidosManager token={token} />,
    ventas: <VentasManager token={token} />,
    facturas: <FacturasManager token={token} puedeGestionar />,
    reportes: <ReportesPanel token={token} />,
    obras: <ObrasManager token={token} puedeEliminar={false} />,
    servicios: <ServiciosManager token={token} puedeEliminar={false} />,
    pqr: <PqrManager token={token} puedeGestionar />,
  };

  return (
    <PanelLayout
      titulo="Operación de la galería"
      descripcion="Gestiona el catálogo, los pedidos, las ventas y la atención al cliente."
      pestanas={PESTANAS}
      activa={pestana}
      onCambiar={setPestana}
    >
      {vistas[pestana]}
    </PanelLayout>
  );
}

export default PanelEmpleado;
