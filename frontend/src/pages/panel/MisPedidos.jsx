import { useState } from "react";
import { CreditCard, Package, ShoppingBag } from "lucide-react";
import { Link } from "react-router-dom";

import { formatoMoneda } from "../../components/graficos/utilidades";
import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Pagination from "../../components/ui/Pagination";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";

const TAMANO_PAGINA = 8;

/** Pedidos y compras del cliente, con el botón de pago de Stripe. */
function MisPedidos({ token }) {
  const toast = useToast();
  const [pagina, setPagina] = useState(1);
  const [pagando, setPagando] = useState(null);

  const pedidos = useRecurso(
    (signal) => api.listarPedidos(token, { page: pagina, page_size: TAMANO_PAGINA }, signal),
    [pagina]
  );

  const ventas = useRecurso(
    (signal) => api.listarVentas(token, { page: 1, page_size: 20 }, signal),
    []
  );

  async function pagar(venta) {
    setPagando(venta.id);
    try {
      const sesion = await api.crearCheckout(venta.id, token);
      // Stripe aloja el formulario de tarjeta: aquí solo redirigimos.
      window.location.href = sesion.checkout_url;
    } catch (error) {
      toast.error(
        error.esValidacion && error.message.includes("STRIPE_SECRET_KEY")
          ? "La pasarela de pago todavía no está configurada en el servidor."
          : error.message
      );
      setPagando(null);
    }
  }

  const porPagar = (ventas.datos?.items ?? []).filter((v) => v.estado === "pendiente_pago");

  return (
    <div className="space-y-6">
      {porPagar.length > 0 && (
        <Card
          titulo="Pendiente de pago"
          descripcion="Completa el pago para que preparemos tu pedido."
          icono={CreditCard}
        >
          <ul className="space-y-3">
            {porPagar.map((venta) => (
              <li
                key={venta.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg
                           border border-aviso/30 bg-aviso-suave/50 p-4"
              >
                <div className="min-w-0">
                  <p className="font-mono text-sm font-medium">{venta.numero}</p>
                  <p className="text-xs text-muted">
                    {venta.detalles.length} línea{venta.detalles.length === 1 ? "" : "s"} ·
                    IVA {formatoMoneda(venta.impuestos)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-base font-bold tabular-nums text-forest">
                    {formatoMoneda(venta.total)}
                  </span>
                  <Button
                    size="sm" iconoIzquierda={CreditCard}
                    cargando={pagando === venta.id} onClick={() => pagar(venta)}
                  >
                    Pagar
                  </Button>
                </div>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-muted">
            El pago se procesa en una página segura de Stripe. Los datos de tu
            tarjeta nunca pasan por nuestros servidores.
          </p>
        </Card>
      )}

      <Card
        titulo={`Mis pedidos${pedidos.datos ? ` (${pedidos.datos.total})` : ""}`}
        descripcion="Aquí aparecen los pedidos que haces desde el catálogo."
        icono={ShoppingBag}
        acciones={
          <Link to="/catalogo">
            <Button size="sm" variant="secundario" iconoIzquierda={Package}>
              Ir al catálogo
            </Button>
          </Link>
        }
      >
        {pedidos.cargando ? (
          <SkeletonFilas filas={3} />
        ) : pedidos.error ? (
          <Alert tipo="error">{pedidos.error.message}</Alert>
        ) : pedidos.datos.items.length === 0 ? (
          <EmptyState
            icono={ShoppingBag}
            titulo="Todavía no has hecho ningún pedido"
            descripcion="Recorre el catálogo y añade las piezas que te interesen."
            accion={
              <Link to="/catalogo">
                <Button iconoIzquierda={Package}>Ver el catálogo</Button>
              </Link>
            }
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

                  {pedido.estado === "pendiente" && (
                    <p className="mt-3 text-xs text-muted">
                      La galería revisará tu pedido y lo confirmará en breve.
                    </p>
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
    </div>
  );
}

export default MisPedidos;
