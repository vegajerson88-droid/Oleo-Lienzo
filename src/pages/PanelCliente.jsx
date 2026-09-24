import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import Button from "../components/ui/Button";

function PanelCliente() {
  const { token, usuario } = useAuth();
  const [obras, setObras] = useState([]);
  const [pedidos, setPedidos] = useState([]);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  async function cargarObras() {
    try {
      const data = await api.listarObras({ page: 1, page_size: 20, disponible: true });
      setObras(data.items);
    } catch (err) {
      setError(err.message);
    }
  }

  async function cargarPedidos() {
    try {
      const data = await api.listarPedidos(token, { page: 1, page_size: 20 });
      setPedidos(data.items);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    cargarObras();
    cargarPedidos();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function comprar(obraId) {
    setMensaje("");
    setError("");
    try {
      await api.crearPedido([{ obra_id: obraId, cantidad: 1 }], token);
      setMensaje("¡Pedido creado correctamente!");
      cargarPedidos();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container mx-auto max-w-6xl px-6 py-10">
      <h1 className="font-display text-3xl mb-1">Hola, {usuario?.nombre}</h1>
      <p className="text-sm text-ink/60 mb-8">Explora obras disponibles y revisa tus pedidos.</p>

      {mensaje && <p className="text-sm text-forest mb-4">{mensaje}</p>}
      {error && <p className="text-sm text-sienna mb-4">{error}</p>}

      <h2 className="font-display text-xl mb-3">Obras disponibles</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        {obras.map((o) => (
          <div key={o.id} className="bg-paper border border-ink/10 rounded-lg p-4 flex flex-col gap-2">
            <p className="font-medium text-sm">{o.titulo}</p>
            <p className="text-xs text-ink/60">{o.artista} · {o.anio} · {o.tecnica}</p>
            <p className="text-sm font-mono">${Number(o.precio).toLocaleString("es-CO")}</p>
            <Button className="mt-2" onClick={() => comprar(o.id)}>Comprar</Button>
          </div>
        ))}
      </div>

      <h2 className="font-display text-xl mb-3">Mis pedidos</h2>
      {pedidos.length === 0 ? (
        <p className="text-sm text-ink/60">Todavía no tienes pedidos.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {pedidos.map((p) => (
            <li key={p.id} className="bg-paper border border-ink/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Pedido #{p.id} · ${Number(p.total).toLocaleString("es-CO")}</p>
                <span className="font-mono text-xs uppercase tracking-wider bg-forest/10 text-forest px-2 py-1 rounded">
                  {p.estado}
                </span>
              </div>
              <ul className="text-xs text-ink/60 mt-1">
                {p.detalles.map((d) => (
                  <li key={d.id}>{d.cantidad} × {d.obra.titulo}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default PanelCliente;
