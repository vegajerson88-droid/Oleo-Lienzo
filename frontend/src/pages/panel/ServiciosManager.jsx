import { useState } from "react";
import { Package, Pencil, Plus, Trash2 } from "lucide-react";

import { formatoMoneda } from "../../components/graficos/utilidades";
import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import Select from "../../components/ui/Select";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import Textarea from "../../components/ui/Textarea";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";
import { validateField } from "../../utils/validators";

const VACIO = { nombre: "", descripcion: "", precio: "", activo: "true" };

function ServiciosManager({ token, puedeEliminar }) {
  const toast = useToast();

  const [modalAbierto, setModalAbierto] = useState(false);
  const [editando, setEditando] = useState(null);
  const [formulario, setFormulario] = useState(VACIO);
  const [errores, setErrores] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [errorFormulario, setErrorFormulario] = useState("");
  const [aEliminar, setAEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);

  const servicios = useRecurso((signal) => api.listarServicios({ page_size: 50 }, signal), []);

  function abrir(servicio) {
    setEditando(servicio);
    setFormulario(
      servicio
        ? {
            nombre: servicio.nombre,
            descripcion: servicio.descripcion,
            precio: String(servicio.precio),
            activo: String(servicio.activo),
          }
        : VACIO
    );
    setErrores({});
    setErrorFormulario("");
    setModalAbierto(true);
  }

  function alCambiar(evento) {
    const { name, value } = evento.target;
    setFormulario((previo) => ({ ...previo, [name]: value }));
    setErrores((previos) => ({ ...previos, [name]: undefined }));
    if (errorFormulario) setErrorFormulario("");
  }

  async function guardar(evento) {
    evento.preventDefault();

    const encontrados = {
      nombre: validateField("nombreServicio", formulario.nombre),
      descripcion: validateField("descripcion", formulario.descripcion),
      precio: validateField("precio", formulario.precio),
    };
    const limpios = Object.fromEntries(Object.entries(encontrados).filter(([, v]) => v));
    setErrores(limpios);
    if (Object.keys(limpios).length > 0) {
      setErrorFormulario("Revisa los campos marcados.");
      return;
    }

    const carga = {
      nombre: formulario.nombre.trim(),
      descripcion: formulario.descripcion.trim(),
      precio: Number(formulario.precio),
      activo: formulario.activo === "true",
    };

    setGuardando(true);
    setErrorFormulario("");
    try {
      if (editando) {
        await api.reemplazarServicio(editando.id, carga, token);
        toast.exito(`«${carga.nombre}» se actualizó.`);
      } else {
        await api.crearServicio(carga, token);
        toast.exito(`«${carga.nombre}» se añadió a los servicios.`);
      }
      setModalAbierto(false);
      servicios.recargar();
    } catch (error) {
      setErrorFormulario(
        error.esConflicto ? "Ya existe un servicio con ese nombre." : error.message
      );
    } finally {
      setGuardando(false);
    }
  }

  async function confirmarEliminacion() {
    setEliminando(true);
    try {
      await api.eliminarServicio(aEliminar.id, token);
      toast.exito(`«${aEliminar.nombre}» se eliminó.`);
      setAEliminar(null);
      servicios.recargar();
    } catch (error) {
      toast.error(
        error.esConflicto
          ? "No se puede eliminar: el servicio ya se vendió. Desactívalo en su lugar."
          : error.message
      );
    } finally {
      setEliminando(false);
    }
  }

  const columnas = [
    {
      clave: "nombre", titulo: "Servicio",
      render: (s) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-ink">{s.nombre}</p>
          <p className="line-clamp-1 text-xs text-muted">{s.descripcion}</p>
        </div>
      ),
    },
    {
      clave: "precio", titulo: "Precio", alinear: "derecha",
      render: (s) => <span className="font-mono text-sm tabular-nums">{formatoMoneda(s.precio)}</span>,
    },
    {
      clave: "activo", titulo: "Estado", alinear: "centro",
      render: (s) => <Badge estado={s.activo ? "activo" : "inactivo"} />,
    },
    {
      clave: "acciones", titulo: "Acciones", alinear: "derecha",
      render: (s) => (
        <div className="flex justify-end gap-1.5">
          <Button size="sm" variant="fantasma" iconoIzquierda={Pencil} onClick={() => abrir(s)}>
            Editar
          </Button>
          {puedeEliminar && (
            <Button
              size="sm" variant="fantasma" iconoIzquierda={Trash2}
              className="text-error hover:bg-error/10" onClick={() => setAEliminar(s)}
            >
              Borrar
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      <Card
        titulo={`Servicios${servicios.datos ? ` (${servicios.datos.total})` : ""}`}
        descripcion="Enmarcado, restauración, envío y asesoría."
        icono={Package}
        acciones={
          <Button size="sm" iconoIzquierda={Plus} onClick={() => abrir(null)}>
            Nuevo servicio
          </Button>
        }
      >
        {servicios.cargando ? (
          <SkeletonFilas filas={4} />
        ) : servicios.error ? (
          <Alert tipo="error">{servicios.error.message}</Alert>
        ) : servicios.datos.items.length === 0 ? (
          <EmptyState
            icono={Package}
            titulo="Todavía no hay servicios"
            accion={<Button iconoIzquierda={Plus} onClick={() => abrir(null)}>Crear el primero</Button>}
          />
        ) : (
          <Table columnas={columnas} filas={servicios.datos.items} claveFila={(s) => s.id} />
        )}
      </Card>

      <Modal
        abierto={modalAbierto}
        onCerrar={() => setModalAbierto(false)}
        titulo={editando ? `Editar «${editando.nombre}»` : "Nuevo servicio"}
        pie={
          <>
            <Button variant="fantasma" onClick={() => setModalAbierto(false)} disabled={guardando}>
              Cancelar
            </Button>
            <Button type="submit" form="formulario-servicio" cargando={guardando}>
              {editando ? "Guardar cambios" : "Crear servicio"}
            </Button>
          </>
        }
      >
        <form id="formulario-servicio" onSubmit={guardar} noValidate className="flex flex-col gap-4">
          <Input label="Nombre" name="nombre" value={formulario.nombre} onChange={alCambiar}
                 error={errores.nombre} maxLength={100} required
                 hint="Debe ser único en el catálogo." />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Precio (COP)" name="precio" type="number" className="sin-flechas"
                   value={formulario.precio} onChange={alCambiar} error={errores.precio} required />
            <Select
              label="Estado" name="activo" value={formulario.activo} onChange={alCambiar}
              options={[
                { value: "true", label: "Activo" },
                { value: "false", label: "Inactivo" },
              ]}
            />
          </div>
          <Textarea label="Descripción" name="descripcion" rows={4}
                    value={formulario.descripcion} onChange={alCambiar}
                    error={errores.descripcion} maxLength={2000} contador required />
          {errorFormulario && <Alert tipo="error">{errorFormulario}</Alert>}
        </form>
      </Modal>

      <Modal
        abierto={Boolean(aEliminar)}
        onCerrar={() => setAEliminar(null)}
        titulo="Eliminar servicio"
        ancho="sm"
        pie={
          <>
            <Button variant="fantasma" onClick={() => setAEliminar(null)} disabled={eliminando}>
              Cancelar
            </Button>
            <Button variant="peligro" cargando={eliminando} onClick={confirmarEliminacion}>
              Sí, eliminar
            </Button>
          </>
        }
      >
        <p className="text-sm text-ink-soft">
          Vas a eliminar <strong className="text-ink">«{aEliminar?.nombre}»</strong>.
          Si ya se vendió alguna vez, el servidor lo impedirá: desactívalo en su lugar.
        </p>
      </Modal>
    </>
  );
}

export default ServiciosManager;
