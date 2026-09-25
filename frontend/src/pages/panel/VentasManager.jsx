import { useState } from "react";
import { Eye, FileText, Filter, Plus, ShoppingCart, X } from "lucide-react";

import { formatoMoneda } from "../../components/graficos/utilidades";
import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import Pagination from "../../components/ui/Pagination";
import Select from "../../components/ui/Select";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import Textarea from "../../components/ui/Textarea";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";

const TAMANO_PAGINA = 10;

const ESTADOS = [
  { value: "", label: "Todos los estados" },
  { value: "pendiente_pago", label: "Pendientes de pago" },
  { value: "pagada", label: "Pagadas" },
  { value: "anulada", label: "Anuladas" },
  { value: "reembolsada", label: "Reembolsadas" },
];

const METODOS_PAGO = [
  { value: "efectivo", label: "Efectivo" },
  { value: "transferencia", label: "Transferencia" },
  { value: "tarjeta", label: "Tarjeta" },
  { value: "otro", label: "Otro" },
];

/** Transiciones válidas, espejo de la máquina de estados del backend. */
const TRANSICIONES = {
  pendiente_pago: ["pagada", "anulada"],
  pagada: ["reembolsada"],
  anulada: [],
  reembolsada: [],
};

const ETIQUETA_ACCION = {
  pagada: "Marcar pagada",
  anulada: "Anular",
  reembolsada: "Reembolsar",
};

const FILTROS_VACIOS = {
  fecha_inicio: "", fecha_fin: "", estado: "", total_min: "", total_max: "",
};

/** Historial de ventas con todos los filtros, y registro de ventas presenciales. */
function VentasManager({ token }) {
  const toast = useToast();

  const [pagina, setPagina] = useState(1);
  const [filtros, setFiltros] = useState(FILTROS_VACIOS);
  const [filtrosAplicados, setFiltrosAplicados] = useState({});
  const [panelFiltros, setPanelFiltros] = useState(false);
  const [detalle, setDetalle] = useState(null);
  const [cambiando, setCambiando] = useState(null);
  const [facturando, setFacturando] = useState(null);
  const [modalVenta, setModalVenta] = useState(false);

  const ventas = useRecurso(
    (signal) =>
      api.listarVentas(token, { page: pagina, page_size: TAMANO_PAGINA, ...filtrosAplicados }, signal),
    [pagina, filtrosAplicados]
  );

  function aplicarFiltros(evento) {
    evento.preventDefault();
    const limpios = Object.fromEntries(Object.entries(filtros).filter(([, v]) => v !== ""));
    setPagina(1);
    setFiltrosAplicados(limpios);
  }

  function limpiarFiltros() {
    setFiltros(FILTROS_VACIOS);
    setFiltrosAplicados({});
    setPagina(1);
  }

  async function cambiarEstado(venta, nuevoEstado) {
    setCambiando(`${venta.id}-${nuevoEstado}`);
    try {
      await api.cambiarEstadoVenta(venta.id, nuevoEstado, token);
      toast.exito(`Venta ${venta.numero}: ${nuevoEstado.replace("_", " ")}.`);
      ventas.recargar();
      setDetalle(null);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setCambiando(null);
    }
  }

  async function emitirFactura(venta) {
    setFacturando(venta.id);
    try {
      const factura = await api.emitirFactura(venta.id, null, token);
      toast.exito(`Factura ${factura.numero} emitida.`);
      ventas.recargar();
      setDetalle(null);
    } catch (error) {
      toast.error(
        error.esConflicto ? "Esta venta ya tiene factura emitida." : error.message
      );
    } finally {
      setFacturando(null);
    }
  }

  const hayFiltros = Object.keys(filtrosAplicados).length > 0;

  const columnas = [
    {
      clave: "numero", titulo: "Venta",
      render: (v) => (
        <div>
          <p className="font-mono text-sm font-medium">{v.numero}</p>
          <p className="text-xs text-muted">
            {new Date(v.creado_en).toLocaleString("es-CO", {
              dateStyle: "short", timeStyle: "short",
            })}
          </p>
        </div>
      ),
    },
    {
      clave: "cliente", titulo: "Cliente",
      render: (v) => (
        <span className="text-sm">
          {v.cliente ? `${v.cliente.nombre} ${v.cliente.apellido}` : `#${v.cliente_id}`}
        </span>
      ),
    },
    {
      clave: "total", titulo: "Total", alinear: "derecha",
      render: (v) => (
        <div>
          <p className="font-mono text-sm font-bold tabular-nums">{formatoMoneda(v.total)}</p>
          <p className="font-mono text-[10px] text-muted">IVA {formatoMoneda(v.impuestos)}</p>
        </div>
      ),
    },
    {
      clave: "estado", titulo: "Estado", alinear: "centro",
      render: (v) => <Badge estado={v.estado} />,
    },
    {
      clave: "factura", titulo: "Factura", alinear: "centro",
      render: (v) =>
        v.factura_numero ? (
          <span className="font-mono text-xs">{v.factura_numero}</span>
        ) : (
          <span className="text-xs text-muted">—</span>
        ),
    },
    {
      clave: "acciones", titulo: "", alinear: "derecha",
      render: (v) => (
        <Button size="sm" variant="fantasma" iconoIzquierda={Eye} onClick={() => setDetalle(v)}>
          Ver
        </Button>
      ),
    },
  ];

  return (
    <>
      <Card
        titulo={`Historial de ventas${ventas.datos ? ` (${ventas.datos.total})` : ""}`}
        descripcion="Filtra por fecha, estado y valor. Desde aquí se emiten las facturas."
        icono={ShoppingCart}
        acciones={
          <div className="flex gap-2">
            <Button
              size="sm" variant="secundario" iconoIzquierda={Filter}
              onClick={() => setPanelFiltros((v) => !v)}
            >
              Filtros
            </Button>
            <Button size="sm" iconoIzquierda={Plus} onClick={() => setModalVenta(true)}>
              Registrar venta
            </Button>
          </div>
        }
      >
        {panelFiltros && (
          <form
            onSubmit={aplicarFiltros}
            className="mb-5 flex flex-wrap items-end gap-3 rounded-lg border border-line/70
                       bg-paper-dim/50 p-4"
          >
            <div className="min-w-[140px] flex-1">
              <Input label="Desde" name="fecha_inicio" type="date" value={filtros.fecha_inicio}
                     onChange={(e) => setFiltros({ ...filtros, fecha_inicio: e.target.value })} />
            </div>
            <div className="min-w-[140px] flex-1">
              <Input label="Hasta" name="fecha_fin" type="date" value={filtros.fecha_fin}
                     onChange={(e) => setFiltros({ ...filtros, fecha_fin: e.target.value })} />
            </div>
            <div className="min-w-[160px] flex-1">
              <Select label="Estado" name="estado" value={filtros.estado} options={ESTADOS}
                      onChange={(e) => setFiltros({ ...filtros, estado: e.target.value })} />
            </div>
            <div className="min-w-[120px] flex-1">
              <Input label="Valor mínimo" name="total_min" type="number" className="sin-flechas"
                     value={filtros.total_min}
                     onChange={(e) => setFiltros({ ...filtros, total_min: e.target.value })} />
            </div>
            <div className="min-w-[120px] flex-1">
              <Input label="Valor máximo" name="total_max" type="number" className="sin-flechas"
                     value={filtros.total_max}
                     onChange={(e) => setFiltros({ ...filtros, total_max: e.target.value })} />
            </div>
            <Button type="submit" className="mb-5">Aplicar</Button>
            {hayFiltros && (
              <Button type="button" variant="fantasma" iconoIzquierda={X}
                      onClick={limpiarFiltros} className="mb-5">
                Limpiar
              </Button>
            )}
          </form>
        )}

        {ventas.cargando ? (
          <SkeletonFilas filas={5} />
        ) : ventas.error ? (
          <Alert tipo="error">{ventas.error.message}</Alert>
        ) : ventas.datos.items.length === 0 ? (
          <EmptyState
            icono={ShoppingCart}
            titulo={hayFiltros ? "Ninguna venta coincide con los filtros" : "Todavía no hay ventas"}
            descripcion="Las ventas se generan al confirmar un pedido, o se registran aquí manualmente."
            accion={
              hayFiltros ? (
                <Button variant="secundario" onClick={limpiarFiltros}>Quitar filtros</Button>
              ) : (
                <Button iconoIzquierda={Plus} onClick={() => setModalVenta(true)}>
                  Registrar una venta
                </Button>
              )
            }
          />
        ) : (
          <>
            <Table columnas={columnas} filas={ventas.datos.items} claveFila={(v) => v.id} />
            <Pagination
              pagina={pagina} tamanoPagina={TAMANO_PAGINA}
              total={ventas.datos.total} onCambiar={setPagina} className="mt-5"
            />
          </>
        )}
      </Card>

      {/* Detalle de la venta */}
      <Modal
        abierto={Boolean(detalle)}
        onCerrar={() => setDetalle(null)}
        titulo={detalle ? `Venta ${detalle.numero}` : ""}
        descripcion={detalle ? `Registrada el ${new Date(detalle.creado_en).toLocaleString("es-CO")}` : ""}
        ancho="lg"
      >
        {detalle && (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-3">
              <Badge estado={detalle.estado} />
              <span className="etiqueta text-muted">
                Pago: {detalle.metodo_pago}
              </span>
              {detalle.pedido_id && (
                <span className="etiqueta text-muted">
                  Desde el pedido #{detalle.pedido_id}
                </span>
              )}
            </div>

            <div>
              <h4 className="mb-2 etiqueta text-muted">Líneas</h4>
              <ul className="divide-y divide-line/60 rounded-lg border border-line/70">
                {detalle.detalles.map((linea) => (
                  <li key={linea.id} className="flex items-center justify-between gap-3 p-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm">{linea.descripcion}</p>
                      <p className="text-xs text-muted">
                        {linea.cantidad} × {formatoMoneda(linea.precio_unitario)}
                        {linea.descuento > 0 && ` · dto. ${formatoMoneda(linea.descuento)}`}
                      </p>
                    </div>
                    <span className="shrink-0 font-mono text-sm tabular-nums">
                      {formatoMoneda(linea.subtotal)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <dl className="space-y-1.5 rounded-lg bg-paper-dim/60 p-4 text-sm">
              {[
                ["Subtotal", detalle.subtotal],
                ...(detalle.descuento > 0 ? [["Descuento", -detalle.descuento]] : []),
                ["IVA (19 %)", detalle.impuestos],
              ].map(([etiqueta, valor]) => (
                <div key={etiqueta} className="flex justify-between text-ink-soft">
                  <dt>{etiqueta}</dt>
                  <dd className="font-mono tabular-nums">{formatoMoneda(valor)}</dd>
                </div>
              ))}
              <div className="flex justify-between border-t border-line pt-2 font-semibold text-forest">
                <dt>Total</dt>
                <dd className="font-mono text-base tabular-nums">{formatoMoneda(detalle.total)}</dd>
              </div>
            </dl>

            {detalle.observaciones && (
              <p className="text-xs italic text-muted">{detalle.observaciones}</p>
            )}

            <div className="flex flex-wrap gap-2 border-t border-line pt-4">
              {(TRANSICIONES[detalle.estado] ?? []).map((destino) => (
                <Button
                  key={destino}
                  size="sm"
                  variant={destino === "pagada" ? "primario" : "peligro"}
                  cargando={cambiando === `${detalle.id}-${destino}`}
                  onClick={() => cambiarEstado(detalle, destino)}
                >
                  {ETIQUETA_ACCION[destino]}
                </Button>
              ))}

              {!detalle.factura_numero && detalle.estado !== "anulada" && (
                <Button
                  size="sm" variant="secundario" iconoIzquierda={FileText}
                  cargando={facturando === detalle.id}
                  onClick={() => emitirFactura(detalle)}
                >
                  Emitir factura
                </Button>
              )}

              {detalle.factura_numero && (
                <Alert tipo="info" className="w-full">
                  Esta venta ya tiene la factura <strong>{detalle.factura_numero}</strong>.
                  Descárgala desde la pestaña «Facturas».
                </Alert>
              )}
            </div>
          </div>
        )}
      </Modal>

      <ModalNuevaVenta
        abierto={modalVenta}
        onCerrar={() => setModalVenta(false)}
        token={token}
        onCreada={() => {
          setModalVenta(false);
          ventas.recargar();
        }}
      />
    </>
  );
}

/** Formulario de registro de una venta presencial. */
function ModalNuevaVenta({ abierto, onCerrar, token, onCreada }) {
  const toast = useToast();
  const [clienteId, setClienteId] = useState("");
  const [lineas, setLineas] = useState([{ tipo: "obra", id: "", cantidad: 1 }]);
  const [descuento, setDescuento] = useState("");
  const [metodoPago, setMetodoPago] = useState("efectivo");
  const [observaciones, setObservaciones] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");

  const clientes = useRecurso(
    (signal) => (abierto ? api.listarUsuarios(token, { rol: "cliente", page_size: 100 }, signal) : null),
    [abierto]
  );
  const obras = useRecurso(
    (signal) => (abierto ? api.listarObras({ disponible: true, page_size: 100 }, signal) : null),
    [abierto]
  );
  const servicios = useRecurso(
    (signal) => (abierto ? api.listarServicios({ activo: true, page_size: 100 }, signal) : null),
    [abierto]
  );

  function actualizarLinea(indice, cambios) {
    setLineas((previas) =>
      previas.map((linea, i) => (i === indice ? { ...linea, ...cambios } : linea))
    );
  }

  async function guardar(evento) {
    evento.preventDefault();
    setError("");

    if (!clienteId) {
      setError("Selecciona el cliente de la venta.");
      return;
    }
    const detalles = lineas
      .filter((linea) => linea.id)
      .map((linea) => ({
        [linea.tipo === "obra" ? "obra_id" : "servicio_id"]: Number(linea.id),
        cantidad: Number(linea.cantidad) || 1,
      }));
    if (detalles.length === 0) {
      setError("Añade al menos una obra o un servicio.");
      return;
    }

    setGuardando(true);
    try {
      const venta = await api.crearVenta(
        {
          cliente_id: Number(clienteId),
          detalles,
          descuento: Number(descuento) || 0,
          metodo_pago: metodoPago,
          observaciones: observaciones.trim() || null,
        },
        token
      );
      toast.exito(`Venta ${venta.numero} registrada por ${formatoMoneda(venta.total)}.`);
      setClienteId("");
      setLineas([{ tipo: "obra", id: "", cantidad: 1 }]);
      setDescuento("");
      setObservaciones("");
      onCreada();
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Modal
      abierto={abierto}
      onCerrar={onCerrar}
      titulo="Registrar una venta"
      descripcion="Para ventas presenciales. El servidor recalcula subtotales e IVA."
      ancho="lg"
      pie={
        <>
          <Button variant="fantasma" onClick={onCerrar} disabled={guardando}>Cancelar</Button>
          <Button type="submit" form="formulario-venta" cargando={guardando}>
            Registrar venta
          </Button>
        </>
      }
    >
      <form id="formulario-venta" onSubmit={guardar} noValidate className="flex flex-col gap-4">
        <Select
          label="Cliente" name="cliente_id" value={clienteId}
          onChange={(evento) => setClienteId(evento.target.value)}
          options={[
            { value: "", label: "Selecciona un cliente…" },
            ...(clientes.datos?.items ?? []).map((c) => ({
              value: String(c.id),
              label: `${c.nombre} ${c.apellido} — ${c.email}`,
            })),
          ]}
          required
        />

        <div>
          <p className="mb-2 etiqueta text-ink-soft">Líneas de la venta</p>
          <div className="space-y-3">
            {lineas.map((linea, indice) => (
              <div key={indice} className="grid grid-cols-1 gap-2 sm:grid-cols-[110px_1fr_90px_auto]">
                <Select
                  name={`tipo-${indice}`} value={linea.tipo}
                  onChange={(e) => actualizarLinea(indice, { tipo: e.target.value, id: "" })}
                  options={[
                    { value: "obra", label: "Obra" },
                    { value: "servicio", label: "Servicio" },
                  ]}
                />
                <Select
                  name={`item-${indice}`} value={linea.id}
                  onChange={(e) => actualizarLinea(indice, { id: e.target.value })}
                  options={[
                    { value: "", label: "Selecciona…" },
                    ...(linea.tipo === "obra"
                      ? (obras.datos?.items ?? []).map((o) => ({
                          value: String(o.id),
                          label: `${o.titulo} — ${formatoMoneda(o.precio)}`,
                        }))
                      : (servicios.datos?.items ?? []).map((s) => ({
                          value: String(s.id),
                          label: `${s.nombre} — ${formatoMoneda(s.precio)}`,
                        }))),
                  ]}
                />
                <Input
                  name={`cantidad-${indice}`} type="number" min="1" className="sin-flechas"
                  value={linea.cantidad}
                  onChange={(e) => actualizarLinea(indice, { cantidad: e.target.value })}
                />
                {lineas.length > 1 && (
                  <Button
                    type="button" variant="fantasma" size="sm"
                    className="text-error"
                    onClick={() => setLineas((previas) => previas.filter((_, i) => i !== indice))}
                  >
                    <X size={14} />
                  </Button>
                )}
              </div>
            ))}
          </div>
          <Button
            type="button" variant="fantasma" size="sm" iconoIzquierda={Plus} className="mt-2"
            onClick={() => setLineas((previas) => [...previas, { tipo: "obra", id: "", cantidad: 1 }])}
          >
            Añadir línea
          </Button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label="Descuento global (COP)" name="descuento" type="number" className="sin-flechas"
            value={descuento} onChange={(e) => setDescuento(e.target.value)}
            hint="No puede superar el subtotal."
          />
          <Select
            label="Método de pago" name="metodo_pago" value={metodoPago}
            onChange={(e) => setMetodoPago(e.target.value)} options={METODOS_PAGO}
          />
        </div>

        <Textarea
          label="Observaciones (opcional)" name="observaciones" rows={2}
          value={observaciones} onChange={(e) => setObservaciones(e.target.value)}
          maxLength={500} contador
        />

        {error && <Alert tipo="error">{error}</Alert>}
      </form>
    </Modal>
  );
}

export default VentasManager;
