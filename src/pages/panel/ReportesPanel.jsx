import { useState } from "react";
import { FileDown, FileSpreadsheet, FileText } from "lucide-react";

import { formatoMoneda } from "../../components/graficos/utilidades";
import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Input from "../../components/ui/Input";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";

function hoyISO() {
  return new Date().toISOString().slice(0, 10);
}

/** Reporte diario de ventas, con exportación a PDF y a Excel. */
function ReportesPanel({ token }) {
  const toast = useToast();
  const [dia, setDia] = useState(hoyISO);
  const [diaConsultado, setDiaConsultado] = useState(hoyISO);
  const [descargando, setDescargando] = useState(null);

  const reporte = useRecurso(
    (signal) => api.reporteDiario(token, diaConsultado, signal),
    [diaConsultado]
  );

  async function descargar(formato) {
    setDescargando(formato);
    try {
      const nombre =
        formato === "pdf"
          ? await api.descargarReportePdf(diaConsultado, token)
          : await api.descargarReporteExcel(diaConsultado, token);
      toast.exito(`Descargado: ${nombre}`);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setDescargando(null);
    }
  }

  const resumen = reporte.datos?.resumen;

  const columnas = [
    {
      clave: "numero", titulo: "Venta",
      render: (v) => (
        <div>
          <p className="font-mono text-sm">{v.numero}</p>
          <p className="text-xs text-muted">
            {new Date(v.fecha_hora).toLocaleTimeString("es-CO", {
              hour: "2-digit", minute: "2-digit",
            })}
          </p>
        </div>
      ),
    },
    { clave: "cliente", titulo: "Cliente", render: (v) => v.cliente ?? "—" },
    {
      clave: "items", titulo: "Productos y servicios",
      render: (v) => (
        <ul className="space-y-0.5 text-xs text-ink-soft">
          {v.items.map((item, i) => (
            <li key={i}>
              {item.cantidad} × {item.descripcion}
            </li>
          ))}
        </ul>
      ),
    },
    {
      clave: "cantidad", titulo: "Unid.", alinear: "centro",
      render: (v) => (
        <span className="font-mono tabular-nums">
          {v.items.reduce((suma, item) => suma + item.cantidad, 0)}
        </span>
      ),
    },
    { clave: "estado", titulo: "Estado", alinear: "centro", render: (v) => <Badge estado={v.estado} /> },
    {
      clave: "total", titulo: "Total", alinear: "derecha",
      render: (v) => (
        <span className="font-mono text-sm font-bold tabular-nums">{formatoMoneda(v.total)}</span>
      ),
    },
  ];

  const tarjetas = resumen
    ? [
        { etiqueta: "Ventas registradas", valor: resumen.ventas_registradas },
        { etiqueta: "Unidades vendidas", valor: resumen.unidades_vendidas },
        { etiqueta: "IVA recaudado", valor: formatoMoneda(resumen.iva) },
        { etiqueta: "Total facturado", valor: formatoMoneda(resumen.total) },
      ]
    : [];

  return (
    <Card
      titulo="Reporte diario de ventas"
      descripcion="Consulta el detalle de un día y expórtalo en PDF o Excel."
      icono={FileText}
      acciones={
        <div className="flex gap-2">
          <Button
            size="sm" variant="secundario" iconoIzquierda={FileDown}
            cargando={descargando === "pdf"} onClick={() => descargar("pdf")}
          >
            PDF
          </Button>
          <Button
            size="sm" variant="secundario" iconoIzquierda={FileSpreadsheet}
            cargando={descargando === "excel"} onClick={() => descargar("excel")}
          >
            Excel
          </Button>
        </div>
      }
    >
      <form
        onSubmit={(evento) => {
          evento.preventDefault();
          setDiaConsultado(dia);
        }}
        className="mb-6 flex flex-wrap items-end gap-3"
      >
        <div className="min-w-[180px]">
          <Input
            label="Fecha del reporte" name="dia" type="date" max={hoyISO()}
            value={dia} onChange={(evento) => setDia(evento.target.value)}
          />
        </div>
        <Button type="submit" className="mb-5">Consultar</Button>
        {dia !== hoyISO() && (
          <Button
            type="button" variant="fantasma" className="mb-5"
            onClick={() => {
              setDia(hoyISO());
              setDiaConsultado(hoyISO());
            }}
          >
            Hoy
          </Button>
        )}
      </form>

      {reporte.cargando ? (
        <SkeletonFilas filas={4} />
      ) : reporte.error ? (
        <Alert tipo="error">{reporte.error.message}</Alert>
      ) : (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            {tarjetas.map(({ etiqueta, valor }) => (
              <div key={etiqueta} className="relative rounded-lg border border-line/70
                                             bg-paper-dim/50 p-4">
                <span className="absolute inset-x-0 top-0 h-[3px] rounded-t-lg bg-gold"
                      aria-hidden="true" />
                <p className="etiqueta text-muted">{etiqueta}</p>
                <p className="mt-1.5 font-display text-xl tabular-nums text-forest">{valor}</p>
              </div>
            ))}
          </div>

          {reporte.datos.ventas.length === 0 ? (
            <EmptyState
              icono={FileText}
              titulo={`No se registraron ventas el ${new Date(
                `${diaConsultado}T00:00:00`
              ).toLocaleDateString("es-CO", { dateStyle: "long" })}`}
              descripcion="Prueba con otra fecha. La exportación seguirá funcionando y generará un reporte vacío."
            />
          ) : (
            <Table columnas={columnas} filas={reporte.datos.ventas} claveFila={(v) => v.numero} />
          )}
        </>
      )}
    </Card>
  );
}

export default ReportesPanel;
