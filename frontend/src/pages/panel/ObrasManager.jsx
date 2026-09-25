import { useState } from "react";
import { Brush, Pencil, Plus, Sparkles, Trash2 } from "lucide-react";

import { formatoMoneda } from "../../components/graficos/utilidades";
import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import Pagination from "../../components/ui/Pagination";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import Textarea from "../../components/ui/Textarea";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";
import { validateForm } from "../../utils/validators";

const TAMANO_PAGINA = 8;
const CAMPOS = ["titulo", "artista", "anio", "tecnica", "precio", "descripcion", "stock"];

const VACIO = {
  titulo: "", artista: "", anio: "", tecnica: "",
  precio: "", descripcion: "", imagen_url: "", stock: "1",
};

/** Gestión del catálogo de obras: crear, editar, eliminar y sugerir precio con IA. */
function ObrasManager({ token, puedeEliminar }) {
  const toast = useToast();

  const [pagina, setPagina] = useState(1);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [editando, setEditando] = useState(null);
  const [formulario, setFormulario] = useState(VACIO);
  const [errores, setErrores] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [errorFormulario, setErrorFormulario] = useState("");
  const [sugerencia, setSugerencia] = useState(null);
  const [pidiendoSugerencia, setPidiendoSugerencia] = useState(false);
  const [aEliminar, setAEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);

  const obras = useRecurso(
    (signal) => api.listarObras({ page: pagina, page_size: TAMANO_PAGINA }, signal),
    [pagina]
  );

  function abrirNueva() {
    setEditando(null);
    setFormulario(VACIO);
    setErrores({});
    setErrorFormulario("");
    setSugerencia(null);
    setModalAbierto(true);
  }

  function abrirEdicion(obra) {
    setEditando(obra);
    setFormulario({
      titulo: obra.titulo, artista: obra.artista, anio: String(obra.anio),
      tecnica: obra.tecnica, precio: String(obra.precio), descripcion: obra.descripcion,
      imagen_url: obra.imagen_url ?? "", stock: String(obra.stock),
    });
    setErrores({});
    setErrorFormulario("");
    setSugerencia(null);
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

    const encontrados = validateForm(formulario, CAMPOS);
    setErrores(encontrados);
    if (Object.keys(encontrados).length > 0) {
      setErrorFormulario("Revisa los campos marcados.");
      return;
    }

    const carga = {
      titulo: formulario.titulo.trim(),
      artista: formulario.artista.trim(),
      anio: Number(formulario.anio),
      tecnica: formulario.tecnica.trim(),
      precio: Number(formulario.precio),
      descripcion: formulario.descripcion.trim(),
      imagen_url: formulario.imagen_url.trim() || null,
      stock: Number(formulario.stock),
      disponible: Number(formulario.stock) > 0,
    };

    setGuardando(true);
    setErrorFormulario("");
    try {
      if (editando) {
        // PUT: el formulario tiene el recurso completo, así que se reemplaza entero.
        await api.reemplazarObra(editando.id, carga, token);
        toast.exito(`«${carga.titulo}» se actualizó correctamente.`);
      } else {
        await api.crearObra(carga, token);
        toast.exito(`«${carga.titulo}» se añadió al catálogo.`);
      }
      setModalAbierto(false);
      obras.recargar();
    } catch (error) {
      setErrorFormulario(error.message);
    } finally {
      setGuardando(false);
    }
  }

  async function confirmarEliminacion() {
    setEliminando(true);
    try {
      await api.eliminarObra(aEliminar.id, token);
      toast.exito(`«${aEliminar.titulo}» se eliminó del catálogo.`);
      setAEliminar(null);
      obras.recargar();
    } catch (error) {
      toast.error(
        error.esConflicto
          ? "No se puede eliminar: la obra ya aparece en pedidos o ventas. Ponla como no disponible."
          : error.message
      );
    } finally {
      setEliminando(false);
    }
  }

  async function pedirSugerencia() {
    if (!formulario.anio || !formulario.tecnica) {
      toast.info("Escribe primero el año y la técnica para poder estimar el precio.");
      return;
    }
    setPidiendoSugerencia(true);
    try {
      const datos = await api.precioSugerido(Number(formulario.anio), formulario.tecnica, token);
      setSugerencia(datos);
      if (datos.disponible) {
        setFormulario((previo) => ({ ...previo, precio: String(Math.round(datos.precio_estimado)) }));
      }
    } catch (error) {
      setSugerencia({ disponible: false, detalle: error.message });
    } finally {
      setPidiendoSugerencia(false);
    }
  }

  const columnas = [
    {
      clave: "titulo", titulo: "Obra",
      render: (obra) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-ink">{obra.titulo}</p>
          <p className="truncate text-xs text-muted">
            {obra.artista} · {obra.anio} · {obra.tecnica}
          </p>
        </div>
      ),
    },
    {
      clave: "precio", titulo: "Precio", alinear: "derecha",
      render: (obra) => (
        <span className="font-mono text-sm tabular-nums">{formatoMoneda(obra.precio)}</span>
      ),
    },
    {
      clave: "stock", titulo: "Stock", alinear: "centro",
      render: (obra) => <span className="font-mono tabular-nums">{obra.stock}</span>,
    },
    {
      clave: "disponible", titulo: "Estado", alinear: "centro",
      render: (obra) => <Badge estado={obra.disponible ? "activo" : "inactivo"} />,
    },
    {
      clave: "acciones", titulo: "Acciones", alinear: "derecha",
      render: (obra) => (
        <div className="flex justify-end gap-1.5">
          <Button size="sm" variant="fantasma" iconoIzquierda={Pencil} onClick={() => abrirEdicion(obra)}>
            Editar
          </Button>
          {puedeEliminar && (
            <Button
              size="sm" variant="fantasma" iconoIzquierda={Trash2}
              className="text-error hover:bg-error/10"
              onClick={() => setAEliminar(obra)}
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
        titulo={`Obras del catálogo${obras.datos ? ` (${obras.datos.total})` : ""}`}
        descripcion="Crea, edita y retira piezas de la colección."
        icono={Brush}
        acciones={
          <Button size="sm" iconoIzquierda={Plus} onClick={abrirNueva}>
            Nueva obra
          </Button>
        }
      >
        {obras.cargando ? (
          <SkeletonFilas filas={5} />
        ) : obras.error ? (
          <Alert tipo="error" titulo="No se pudieron cargar las obras">
            {obras.error.message}
          </Alert>
        ) : obras.datos.items.length === 0 ? (
          <EmptyState
            icono={Brush}
            titulo="El catálogo está vacío"
            descripcion="Añade la primera obra para que aparezca en la galería."
            accion={<Button iconoIzquierda={Plus} onClick={abrirNueva}>Nueva obra</Button>}
          />
        ) : (
          <>
            <Table columnas={columnas} filas={obras.datos.items} claveFila={(o) => o.id} />
            <Pagination
              pagina={pagina} tamanoPagina={TAMANO_PAGINA}
              total={obras.datos.total} onCambiar={setPagina} className="mt-5"
            />
          </>
        )}
      </Card>

      {/* Crear / editar */}
      <Modal
        abierto={modalAbierto}
        onCerrar={() => setModalAbierto(false)}
        titulo={editando ? `Editar «${editando.titulo}»` : "Nueva obra"}
        descripcion={
          editando
            ? "Se envía el recurso completo (PUT), así que revisa todos los campos."
            : "Todos los campos marcados son obligatorios."
        }
        ancho="lg"
        pie={
          <>
            <Button variant="fantasma" onClick={() => setModalAbierto(false)} disabled={guardando}>
              Cancelar
            </Button>
            <Button type="submit" form="formulario-obra" cargando={guardando}>
              {editando ? "Guardar cambios" : "Crear obra"}
            </Button>
          </>
        }
      >
        <form id="formulario-obra" onSubmit={guardar} noValidate className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Título" name="titulo" value={formulario.titulo} onChange={alCambiar}
                   error={errores.titulo} maxLength={120} required />
            <Input label="Artista" name="artista" value={formulario.artista} onChange={alCambiar}
                   error={errores.artista} maxLength={80} required />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Input label="Año" name="anio" type="number" className="sin-flechas"
                   value={formulario.anio} onChange={alCambiar} error={errores.anio} required />
            <Input label="Técnica" name="tecnica" value={formulario.tecnica} onChange={alCambiar}
                   error={errores.tecnica} maxLength={80} required />
            <Input label="Stock" name="stock" type="number" min="0" className="sin-flechas"
                   value={formulario.stock} onChange={alCambiar} error={errores.stock}
                   hint="0 la marca como no disponible." required />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_auto] sm:items-start">
            <Input label="Precio (COP)" name="precio" type="number" className="sin-flechas"
                   value={formulario.precio} onChange={alCambiar} error={errores.precio} required />
            <Button
              type="button" variant="secundario" iconoIzquierda={Sparkles}
              cargando={pidiendoSugerencia} onClick={pedirSugerencia} className="sm:mt-6"
            >
              Sugerir con IA
            </Button>
          </div>

          {sugerencia && (
            <Alert tipo={sugerencia.disponible ? "info" : "aviso"}>
              {sugerencia.disponible ? (
                <>
                  Precio estimado por el modelo propio:{" "}
                  <strong>{formatoMoneda(sugerencia.precio_estimado)}</strong>. Se calculó
                  con {sugerencia.variables_utilizadas?.join(" y ")} (modelo{" "}
                  {sugerencia.version_modelo}). Puedes ajustarlo antes de guardar.
                </>
              ) : (
                sugerencia.detalle
              )}
            </Alert>
          )}

          <Input label="URL de la imagen (opcional)" name="imagen_url"
                 value={formulario.imagen_url} onChange={alCambiar} maxLength={255}
                 placeholder="https://…" />

          <Textarea label="Descripción" name="descripcion" rows={4}
                    value={formulario.descripcion} onChange={alCambiar}
                    error={errores.descripcion} maxLength={2000} contador required />

          {errorFormulario && <Alert tipo="error">{errorFormulario}</Alert>}
        </form>
      </Modal>

      {/* Confirmación de borrado */}
      <Modal
        abierto={Boolean(aEliminar)}
        onCerrar={() => setAEliminar(null)}
        titulo="Eliminar obra"
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
          Vas a eliminar <strong className="text-ink">«{aEliminar?.titulo}»</strong> del
          catálogo. Esta acción no se puede deshacer.
        </p>
        <Alert tipo="aviso" className="mt-4">
          Si la obra ya aparece en algún pedido o venta, el servidor rechazará el
          borrado para no romper el histórico. En ese caso, ponle stock 0 para
          retirarla de la galería conservando su historia.
        </Alert>
      </Modal>
    </>
  );
}

export default ObrasManager;
