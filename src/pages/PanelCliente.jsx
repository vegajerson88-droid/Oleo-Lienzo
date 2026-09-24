import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BarChart3, FileText, MessageSquareWarning, ShoppingBag } from "lucide-react";

import Alert from "../components/ui/Alert";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import PanelLayout from "./PanelLayout";
import DashboardPanel from "./panel/DashboardPanel";
import FacturasManager from "./panel/FacturasManager";
import MisPedidos from "./panel/MisPedidos";
import PqrManager from "./panel/PqrManager";

const PESTANAS = [
  { id: "pedidos", label: "Mis pedidos", icono: ShoppingBag },
  { id: "facturas", label: "Mis facturas", icono: FileText },
  { id: "pqr", label: "Mis PQR", icono: MessageSquareWarning },
  { id: "resumen", label: "Resumen", icono: BarChart3 },
];

/** Panel del cliente: solo su propia actividad. */
function PanelCliente() {
  const { token, usuario } = useAuth();
  const toast = useToast();
  const [pestana, setPestana] = useState("pedidos");
  const [parametros, setParametros] = useSearchParams();

  // Stripe devuelve al cliente aquí con ?pago=exitoso o ?pago=cancelado.
  const resultadoPago = parametros.get("pago");
  const ventaPagada = parametros.get("venta");

  useEffect(() => {
    if (!resultadoPago) return;
    if (resultadoPago === "exitoso") {
      toast.exito(
        ventaPagada
          ? `Pago recibido para la venta ${ventaPagada}. ¡Gracias por tu compra!`
          : "Pago recibido. ¡Gracias por tu compra!"
      );
    } else {
      toast.aviso("El pago se canceló. Tu pedido sigue pendiente.");
    }
    // Limpia la URL para que el aviso no reaparezca al recargar.
    parametros.delete("pago");
    parametros.delete("venta");
    setParametros(parametros, { replace: true });
  }, [resultadoPago, ventaPagada, parametros, setParametros, toast]);

  const vistas = {
    pedidos: <MisPedidos token={token} />,
    facturas: <FacturasManager token={token} />,
    pqr: <PqrManager token={token} />,
    resumen: <DashboardPanel token={token} />,
  };

  return (
    <PanelLayout
      titulo={`Hola, ${usuario?.nombre}`}
      descripcion="Consulta tus pedidos, descarga tus facturas y haz seguimiento a tus solicitudes."
      pestanas={PESTANAS}
      activa={pestana}
      onCambiar={setPestana}
    >
      {resultadoPago === "exitoso" && (
        <Alert tipo="exito" titulo="Pago confirmado" className="mb-5">
          Recibimos tu pago. Te enviamos la confirmación por correo y ya puedes
          descargar la factura desde «Mis facturas» en cuanto se emita.
        </Alert>
      )}
      {vistas[pestana]}
    </PanelLayout>
  );
}

export default PanelCliente;
