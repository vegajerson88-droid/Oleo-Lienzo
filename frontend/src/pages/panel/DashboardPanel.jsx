import { useEffect, useState } from "react";
import {
  BarChart3, Brush, FileText, MessageSquareWarning, Package,
  RefreshCw, ShoppingCart, Users, Wallet,
} from "lucide-react";

import GraficoBarras from "../../components/graficos/GraficoBarras";
import GraficoLinea from "../../components/graficos/GraficoLinea";
import StatCard from "../../components/graficos/StatCard";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";

/** Icono asociado a cada indicador, para que la tarjeta se lea de un vistazo. */
const ICONOS = {
  total_usuarios: Users, usuarios_activos: Users,
  total_obras: Brush, obras_disponibles: Brush,
  total_servicios: Package, total_ventas: ShoppingCart,
  ingresos: Wallet, total_facturado: Wallet, total_facturas: FileText,
  pqr_recibidas: MessageSquareWarning, pqr_pendientes: MessageSquareWarning,
  total_pedidos: Package, mis_pedidos: Package, mis_compras: ShoppingCart,
  total_invertido: Wallet, mis_facturas: FileText,
  mis_pqr_abiertas: MessageSquareWarning,
};

/** Los gráficos de importes se formatean como moneda; los de conteo, no. */
const GRAFICOS_DE_DINERO = new Set([
  "Ventas por día", "Mis compras por día", "Productos y servicios más vendidos",
]);

/** Estados de venta por los que se puede filtrar, tal como los nombra la API. */
const ESTADOS_VENTA = [
  { value: "", label: "Todos los estados" },
  { value: "pendiente_pago", label: "Pendiente de pago" },
  { value: "pagada", label: "Pagada" },
  { value: "anulada", label: "Anulada" },
  { value: "reembolsada", label: "Reembolsada" },
];

const FILTROS_VACIOS = {
  fecha_inicio: "", fecha_fin: "", obra_id: "", servicio_id: "", estado: "", cliente_id: "",
};

/** Quita los campos vacíos: la API solo debe recibir los filtros realmente usados. */
function soloLosRellenos(filtros) {
  return Object.fromEntries(Object.entries(filtros).filter(([, valor]) => valor !== ""));
}

/**
 * Dashboard.
 *
 * Toda la información viene del endpoint `/api/dashboard`, que decide qué
 * indicadores y gráficos corresponden al rol de quien consulta. Aquí no hay
 * ni un solo número escrito a mano.
 */
function DashboardPanel({ token, rol }) {
  const [filtros, setFiltros] = useState(FILTROS_VACIOS);
  const [filtrosAplicados, setFiltrosAplicados] = useState({});
  // Opciones de los desplegables: se piden a la API, no se escriben a mano.
  const [opciones, setOpciones] = useState({ obras: [], servicios: [], clientes: [] });

  const esAdmin = rol === "administrador";

  const { datos, cargando, error, recargar } = useRecurso(
    (signal) => api.dashboard(token, filtrosAplicados, signal),
    [filtrosAplicados]
  );

  useEffect(() => {
    const control = new AbortController();

    async function cargarOpciones() {
      try {
        const [obras, servicios, usuarios] = await Promise.all([
          api.listarObras({ page_size: 100 }, control.signal),
          api.listarServicios({ page_size: 100 }, control.signal),
          // Solo el administrador puede listar usuarios para filtrar por cliente.
          esAdmin
            ? api.listarUsuarios(token, { page_size: 100 }, control.signal)
            : Promise.resolve({ items: [] }),
        ]);
        setOpciones({
          obras: obras.items ?? [],
          servicios: servicios.items ?? [],
          clientes: (usuarios.items ?? []).filter((u) => u.rol?.nombre === "cliente"),
        });
      } catch {
        // Sin opciones el dashboard sigue siendo usable: solo se filtra por fecha.
      }
    }

    cargarOpciones();
    return () => control.abort();
  }, [token, esAdmin]);

  function cambiar(campo) {
    return (evento) => setFiltros((previos) => ({ ...previos, [campo]: evento.target.value }));
  }

  function aplicarFiltros(evento) {
    evento.preventDefault();
    setFiltrosAplicados(soloLosRellenos(filtros));
  }

  function limpiarFiltros() {
    setFiltros(FILTROS_VACIOS);
    setFiltrosAplicados({});
  }

  if (error) {
    return (
      <Alert tipo="error" titulo="No se pudo cargar el dashboard">
        {error.message}
        <Button variant="fantasma" size="sm" onClick={recargar} className="ml-2">
          Reintentar
        </Button>
      </Alert>
    );
  }

  const hayFiltros = Object.keys(filtrosAplicados).length > 0;

  return (
    <div className="space-y-6">
      {/* Filtros: fecha, producto, servicio, estado y cliente */}
      <form
        onSubmit={aplicarFiltros}
        className="space-y-3 rounded-xl border border-line/70 bg-paper-dim/50 p-4"
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Input
            label="Desde" name="fecha_inicio" type="date"
            value={filtros.fecha_inicio} onChange={cambiar("fecha_inicio")}
          />
          <Input
            label="Hasta" name="fecha_fin" type="date"
            value={filtros.fecha_fin} onChange={cambiar("fecha_fin")}
          />
          <Select
            label="Estado de la venta" name="estado"
            value={filtros.estado} onChange={cambiar("estado")}
            options={ESTADOS_VENTA}
          />
          <Select
            label="Obra" name="obra_id"
            value={filtros.obra_id} onChange={cambiar("obra_id")}
            options={[
              { value: "", label: "Todas las obras" },
              ...opciones.obras.map((o) => ({ value: String(o.id), label: o.titulo })),
            ]}
          />
          <Select
            label="Servicio" name="servicio_id"
            value={filtros.servicio_id} onChange={cambiar("servicio_id")}
            options={[
              { value: "", label: "Todos los servicios" },
              ...opciones.servicios.map((s) => ({ value: String(s.id), label: s.nombre })),
            ]}
          />
          {esAdmin && (
            <Select
              label="Cliente" name="cliente_id"
              value={filtros.cliente_id} onChange={cambiar("cliente_id")}
              options={[
                { value: "", label: "Todos los clientes" },
                ...opciones.clientes.map((c) => ({
                  value: String(c.id),
                  label: `${c.nombre} ${c.apellido}`,
                })),
              ]}
            />
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit">Aplicar filtros</Button>
          {hayFiltros && (
            <Button type="button" variant="fantasma" onClick={limpiarFiltros}>
              Todo el histórico
            </Button>
          )}
          <Button
            type="button" variant="secundario" iconoIzquierda={RefreshCw}
            onClick={recargar} cargando={cargando} className="ml-auto"
          >
            Actualizar
          </Button>
        </div>
      </form>

      {/* Tarjetas de indicadores */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cargando && !datos
          ? Array.from({ length: 4 }).map((_, i) => <StatCard key={i} cargando />)
          : (datos?.indicadores ?? []).map((indicador) => (
              <StatCard
                key={indicador.clave}
                etiqueta={indicador.etiqueta}
                valor={indicador.valor}
                formato={indicador.formato}
                variacion={indicador.variacion}
                icono={ICONOS[indicador.clave]}
              />
            ))}
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {(datos?.graficos ?? []).map((grafico) => (
          <Card
            key={grafico.nombre}
            titulo={grafico.nombre}
            icono={BarChart3}
            descripcion={
              grafico.tipo === "linea"
                ? "Evolución en el tiempo. Pasa el ratón para ver el dato exacto."
                : "Comparación por categoría."
            }
            className={grafico.tipo === "linea" ? "lg:col-span-2" : ""}
          >
            {grafico.tipo === "linea" ? (
              <GraficoLinea
                puntos={grafico.puntos}
                formato={GRAFICOS_DE_DINERO.has(grafico.nombre) ? "moneda" : "numero"}
              />
            ) : (
              <GraficoBarras
                puntos={grafico.puntos}
                formato={GRAFICOS_DE_DINERO.has(grafico.nombre) ? "moneda" : "numero"}
              />
            )}
          </Card>
        ))}
      </div>

      {datos && (
        <p className="text-center text-xs text-muted">
          Datos calculados en la base de datos
          {datos.periodo_inicio || datos.periodo_fin
            ? ` para el periodo ${datos.periodo_inicio ?? "inicio"} – ${datos.periodo_fin ?? "hoy"}.`
            : " sobre todo el histórico."}
        </p>
      )}
    </div>
  );
}

export default DashboardPanel;
