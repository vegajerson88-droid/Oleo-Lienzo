import { useState } from "react";
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

/**
 * Dashboard.
 *
 * Toda la información viene del endpoint `/api/dashboard`, que decide qué
 * indicadores y gráficos corresponden al rol de quien consulta. Aquí no hay
 * ni un solo número escrito a mano.
 */
function DashboardPanel({ token }) {
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [filtrosAplicados, setFiltrosAplicados] = useState({});

  const { datos, cargando, error, recargar } = useRecurso(
    (signal) => api.dashboard(token, filtrosAplicados, signal),
    [filtrosAplicados]
  );

  function aplicarFiltros(evento) {
    evento.preventDefault();
    setFiltrosAplicados({
      fecha_inicio: fechaInicio || undefined,
      fecha_fin: fechaFin || undefined,
    });
  }

  function limpiarFiltros() {
    setFechaInicio("");
    setFechaFin("");
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

  const hayFiltros = Boolean(filtrosAplicados.fecha_inicio || filtrosAplicados.fecha_fin);

  return (
    <div className="space-y-6">
      {/* Filtros: una sola fila sobre los gráficos */}
      <form
        onSubmit={aplicarFiltros}
        className="flex flex-wrap items-end gap-3 rounded-xl border border-line/70
                   bg-paper-dim/50 p-4"
      >
        <div className="min-w-[150px] flex-1">
          <Input
            label="Desde" name="fecha_inicio" type="date"
            value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)}
          />
        </div>
        <div className="min-w-[150px] flex-1">
          <Input
            label="Hasta" name="fecha_fin" type="date"
            value={fechaFin} onChange={(e) => setFechaFin(e.target.value)}
          />
        </div>
        <Button type="submit" className="mb-5">Aplicar</Button>
        {hayFiltros && (
          <Button type="button" variant="fantasma" onClick={limpiarFiltros} className="mb-5">
            Todo el histórico
          </Button>
        )}
        <Button
          type="button" variant="secundario" iconoIzquierda={RefreshCw}
          onClick={recargar} cargando={cargando} className="mb-5 ml-auto"
        >
          Actualizar
        </Button>
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
