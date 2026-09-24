import { useEffect, useState } from "react";
import { api } from "../../services/api";
import Button from "../../components/ui/Button";

const TRANSICIONES = {
  pendiente: ["confirmado", "cancelado"],
  confirmado: ["entregado", "cancelado"],
  entregado: [],
  cancelado: [],
};

const ESTADO_LABEL = {
  pendiente: "Pendiente", confirmado: "Confirmado", entregado: "Entregado", cancelado: "Cancelado",
};

function PedidosManager({ token }) {
  const [pedidos, setPedidos] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  async function cargar() {
    setCargando(true);
    try {
      const data = await api.listarPedidos(token, { page: 1, page_size: 50 });
      setPedidos(data.items);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { cargar(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function cambiarEstado(pedidoId, nuevoEstado) {
    setError("");
    try {
      await api.cambiarEstadoPedido(pedidoId, nuevoEstado, token);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="bg-paper border border-ink/10 rounded-lg p-5">
      <h3 className="font-display text-lg mb-3">Pedidos ({pedidos.length})</h3>
      {error && <p className="text-sm text-sienna mb-3">{error}</p>}
      {cargando ? (
        <p className="text-sm text-ink/60">Cargando...</p>
      ) : pedidos.length === 0 ? (
        <p className="text-sm text-ink/60">Todavía no hay pedidos.</p>
      ) : (
        <ul className="flex flex-col gap-4">
          {pedidos.map((p) => (
            <li key={p.id} className="border-b border-ink/10 pb-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <p className="text-sm font-medium">
                  Pedido #{p.id} · Cliente #{p.cliente_id} · ${Number(p.total).toLocaleString("es-CO")}
                </p>
                <span className="font-mono text-xs uppercase tracking-wider bg-forest/10 text-forest px-2 py-1 rounded">
                  {ESTADO_LABEL[p.estado] || p.estado}
                </span>
              </div>
              <ul className="text-xs text-ink/60 mt-1 mb-2">
                {p.detalles.map((d) => (
                  <li key={d.id}>{d.cantidad} × {d.obra.titulo} (${Number(d.precio_unitario).toLocaleString("es-CO")})</li>
                ))}
              </ul>
              <div className="flex gap-2">
                {(TRANSICIONES[p.estado] || []).map((estado) => (
                  <Button
                    key={estado}
                    variant="outline"
                    className="!px-3 !py-1.5 text-xs"
                    onClick={() => cambiarEstado(p.id, estado)}
                  >
                    Marcar como {ESTADO_LABEL[estado]}
                  </Button>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default PedidosManager;
