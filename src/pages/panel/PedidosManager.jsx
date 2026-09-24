import { useState } from "react";
import { Package, ShoppingCart } from "lucide-react";

import { formatoMoneda } from "../../components/graficos/utilidades";
import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Pagination from "../../components/ui/Pagination";
import Select from "../../components/ui/Select";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";

const TAMANO_PAGINA = 10;

/**
 * Transiciones que la interfaz ofrece en cada estado.
 *
 * Es una copia de la máquina de estados del backend, solo para no mostrar
 * botones que van a fallar. La transición la valida el servidor igualmente.
 */
const TRANSICIONES = {
  pendiente: ["confirmado", "cancelado"],
  confirmado: ["entregado", "cancelado"],
  entregado: [],
  cancelado: [],
};

const ETIQUETA_ACCION = {
  confirmado: "Confirmar",
  entregado: "Marcar entregado",
  cancelado: "Cancelar",
};

const FILTROS_ESTADO = [
  { value: "", label: "Todos los estados" },
  { value: "pendiente", label: "Pendientes" },
  { value: "confirmado", label: "Confirmados" },
  { value: "entregado", label: "Entregados" },
  { value: "cancelado", label: "Cancelados" },
];

function PedidosManager({ token }) {
  const toast = useToast();
  const [pagina, setPagina] = useState(1);
  const [estado, setEstado] = useState("");
  const [cambiando, setCambiando] = useState(null);

  const pedidos = useRecurso(
    (signal) =>
      api.listarPedidos(
        token,
        { page: pagina, page_size: TAMANO_PAGINA, estado: estado || undefined },
        signal
      ),
    [pagina, estado]
  );

  async function cambiarEstado(pedido, nuevoEstado) {
    setCambiando(`${pedido.id}-${nuevoEstado}`);
    try {
      await api.cambiarEstadoPedido(pedido.id, nuevoEstado, token);
      toast.exito(
        nuevoEstado === "confirmado"
          ? `Pedido #${pedido.id} confirmado. Se generó su venta automáticamente.`
          : `Pedido #${pedido.id}: ${nuevoEstado}.`
      );
      pedidos.recargar();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setCambiando(null);
    }
  }

  return (
    <Card
      titulo={`Pedidos${pedidos.datos ? ` (${pedidos.datos.total})` : ""}`}
      descripcion="Confirmar un pedido genera su venta. Cancelarlo devuelve el inventario."
      icono={ShoppingCart}
      acciones={
        <div className="w-44">
          <Select
            name="estado"
            value={estado}
            onChange={(evento) => {
              setEstado(evento.target.value);
              setPagina(1);
            }}
            options={FILTROS_ESTADO}
          />
        </div>
      }
    >
      {pedidos.cargando ? (
        <SkeletonFilas filas={4} />
      ) : pedidos.error ? (
        <Alert tipo="error">{pedidos.error.message}</Alert>
      ) : pedidos.datos.items.length === 0 ? (
        <EmptyState
          icono={Package}
          titulo={estado ? `No hay pedidos ${estado}s` : "Todavía no hay pedidos"}
          descripcion="Los pedidos aparecen aquí en cuanto un cliente los hace desde el catálogo."
        />
      ) : (
        <>
          <ul className="flex flex-col gap-4">
            {pedidos.datos.items.map((pedido) => (
              <li key={pedido.id} className="rounded-lg border border-line/70 bg-paper-dim/30 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-display text-base">
                      Pedido #{pedido.id}
                      <span className="ml-2 font-mono text-sm font-normal tabular-nums text-forest">
                        {formatoMoneda(pedido.total)}
                      </span>
                    </p>
                    <p className="mt-0.5 text-xs text-muted">
                      Cliente #{pedido.cliente_id} ·{" "}
                      {new Date(pedido.creado_en).toLocaleString("es-CO", {
                        dateStyle: "medium", timeStyle: "short",
                      })}
                    </p>
                  </div>
                  <Badge estado={pedido.estado} />
                </div>

                <ul className="mt-3 space-y-1 border-t border-line/60 pt-3">
                  {pedido.detalles.map((detalle) => (
                    <li key={detalle.id} className="flex justify-between gap-3 text-xs">
                      <span className="min-w-0 truncate text-ink-soft">
                        {detalle.cantidad} × {detalle.descripcion}
                      </span>
                      <span className="shrink-0 font-mono tabular-nums text-muted">
                        {formatoMoneda(detalle.subtotal)}
                      </span>
                    </li>
                  ))}
                </ul>

                {TRANSICIONES[pedido.estado]?.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2 border-t border-line/60 pt-3">
                    {TRANSICIONES[pedido.estado].map((destino) => (
                      <Button
                        key={destino}
                        size="sm"
                        variant={destino === "cancelado" ? "peligro" : "secundario"}
                        cargando={cambiando === `${pedido.id}-${destino}`}
                        onClick={() => cambiarEstado(pedido, destino)}
                      >
                        {ETIQUETA_ACCION[destino]}
                      </Button>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>

          <Pagination
            pagina={pagina} tamanoPagina={TAMANO_PAGINA}
            total={pedidos.datos.total} onCambiar={setPagina} className="mt-5"
          />
        </>
      )}
    </Card>
  );
}

export default PedidosManager;
