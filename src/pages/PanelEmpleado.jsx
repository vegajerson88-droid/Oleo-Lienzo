import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import ObrasManager from "./panel/ObrasManager";
import ServiciosManager from "./panel/ServiciosManager";
import PedidosManager from "./panel/PedidosManager";

const TABS = [
  { id: "obras", label: "Obras" },
  { id: "servicios", label: "Servicios" },
  { id: "pedidos", label: "Pedidos" },
];

function PanelEmpleado() {
  const { token, usuario } = useAuth();
  const [tab, setTab] = useState("obras");

  return (
    <div className="container mx-auto max-w-6xl px-6 py-10">
      <h1 className="font-display text-3xl mb-1">Panel de Empleado</h1>
      <p className="text-sm text-ink/60 mb-8">Hola, {usuario?.nombre}. Gestiona obras, servicios y pedidos.</p>

      <div className="flex gap-2 mb-6 border-b border-ink/10">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`font-mono text-xs uppercase tracking-wider px-4 py-3 border-b-2 transition-colors ${
              tab === t.id ? "border-gold text-forest" : "border-transparent text-ink/50 hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "obras" && <ObrasManager token={token} puedeEliminar={false} />}
      {tab === "servicios" && <ServiciosManager token={token} puedeEliminar={false} />}
      {tab === "pedidos" && <PedidosManager token={token} />}
    </div>
  );
}

export default PanelEmpleado;
