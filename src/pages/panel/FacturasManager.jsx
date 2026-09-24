import { useState } from "react";
import { Download, FileText, Search } from "lucide-react";

import { formatoMoneda } from "../../components/graficos/utilidades";
import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Input from "../../components/ui/Input";
import Pagination from "../../components/ui/Pagination";
import Select from "../../components/ui/Select";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";

const TAMANO_PAGINA = 10;

const ESTADOS = [
  { value: "", label: "Todos los estados" },
  { value: "emitida", label: "Emitidas" },
  { value: "pagada", label: "Pagadas" },
  { value: "anulada", label: "Anuladas" },
];

/** Consulta y descarga de facturas. El cliente solo ve las suyas. */
function FacturasManager({ token, puedeGestionar = false }) {
  const toast = useToast();

  const [pagina, setPagina] = useState(1);
  const [buscar, setBuscar] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [estado, setEstado] = useState("");
  const [descargando, setDescargando] = useState(null);
  const [cambiando, setCambiando] = useState(null);

  const facturas = useRecurso(
    (signal) =>
      api.listarFacturas(
        token,
        {
          page: pagina, page_size: TAMANO_PAGINA,
          buscar: busquedaAplicada || undefined,
          estado: estado || undefined,
        },
        signal
      ),
    [pagina, busquedaAplicada, estado]
  );

  async function descargar(factura) {
    setDescargando(factura.id);
    try {
      const nombre = await api.descargarFacturaPdf(factura.id, factura.numero, token);
      toast.exito(`Descargado: ${nombre}`);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setDescargando(null);
    }
  }

  async function cambiarEstado(factura, nuevoEstado) {
    setCambiando(factura.id);
    try {
      await api.cambiarEstadoFactura(factura.id, nuevoEstado, token);
      toast.exito(`Factura ${factura.numero}: ${nuevoEstado}.`);
      facturas.recargar();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setCambiando(null);
    }
  }

  const columnas = [
    {
      clave: "numero", titulo: "Factura",
      render: (f) => (
        <div>
          <p className="font-mono text-sm font-medium">{f.numero}</p>
          <p className="text-xs text-muted">
            {new Date(f.fecha_emision).toLocaleDateString("es-CO", { dateStyle: "medium" })}
          </p>
        </div>
      ),
    },
    {
      clave: "cliente_nombre", titulo: "Cliente",
      render: (f) => (
        <div className="min-w-0">
          <p className="truncate text-sm">{f.cliente_nombre}</p>
          <p className="truncate text-xs text-muted">{f.cliente_documento}</p>
        </div>
      ),
    },
    {
      clave: "total", titulo: "Total", alinear: "derecha",
      render: (f) => (
        <div>
          <p className="font-mono text-sm font-bold tabular-nums">{formatoMoneda(f.total)}</p>
          <p className="font-mono text-[10px] text-muted">
            IVA {formatoMoneda(f.impuestos)}
          </p>
        </div>
      ),
    },
    {
      clave: "estado", titulo: "Estado", alinear: "centro",
      render: (f) => <Badge estado={f.estado} />,
    },
    {
      clave: "acciones", titulo: "Acciones", alinear: "derecha",
      render: (f) => (
        <div className="flex flex-wrap justify-end gap-1.5">
          <Button
            size="sm" variant="secundario" iconoIzquierda={Download}
            cargando={descargando === f.id} onClick={() => descargar(f)}
          >
            PDF
          </Button>
          {puedeGestionar && f.estado === "emitida" && (
            <Button
              size="sm" variant="fantasma"
              cargando={cambiando === f.id}
              onClick={() => cambiarEstado(f, "pagada")}
            >
              Marcar pagada
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <Card
      titulo={`Facturas${facturas.datos ? ` (${facturas.datos.total})` : ""}`}
      descripcion="Busca por número, cliente o documento y descarga el PDF."
      icono={FileText}
    >
      <form
        onSubmit={(evento) => {
          evento.preventDefault();
          setPagina(1);
          setBusquedaAplicada(buscar.trim());
        }}
        className="mb-5 flex flex-wrap items-end gap-3"
      >
        <div className="min-w-[180px] flex-1">
          <Input
            label="Buscar" name="buscar" value={buscar}
            onChange={(evento) => setBuscar(evento.target.value)}
            placeholder="OL-000001, nombre o documento…" maxLength={80}
          />
        </div>
        <div className="min-w-[160px]">
          <Select
            label="Estado" name="estado" value={estado}
            onChange={(evento) => {
              setEstado(evento.target.value);
              setPagina(1);
            }}
            options={ESTADOS}
          />
        </div>
        <Button type="submit" iconoIzquierda={Search} className="mb-5">
          Buscar
        </Button>
      </form>

      {facturas.cargando ? (
        <SkeletonFilas filas={5} />
      ) : facturas.error ? (
        <Alert tipo="error">{facturas.error.message}</Alert>
      ) : facturas.datos.items.length === 0 ? (
        <EmptyState
          icono={FileText}
          titulo="No hay facturas que coincidan"
          descripcion="Las facturas se emiten desde el módulo de ventas."
        />
      ) : (
        <>
          <Table columnas={columnas} filas={facturas.datos.items} claveFila={(f) => f.id} />
          <Pagination
            pagina={pagina} tamanoPagina={TAMANO_PAGINA}
            total={facturas.datos.total} onCambiar={setPagina} className="mt-5"
          />
        </>
      )}
    </Card>
  );
}

export default FacturasManager;
