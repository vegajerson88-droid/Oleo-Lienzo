import { useState } from "react";
import { Link } from "react-router-dom";
import { Brush, Filter, Search, ShoppingBag, X } from "lucide-react";

import Alert from "../components/ui/Alert";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Pagination from "../components/ui/Pagination";
import Select from "../components/ui/Select";
import { SkeletonFilas } from "../components/ui/Skeleton";
import { formatoMoneda } from "../components/graficos/utilidades";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useRecurso } from "../hooks/useRecurso";
import { api } from "../services/api";

const TAMANO_PAGINA = 9;

const ORDENES = [
  { value: "", label: "Más recientes" },
  { value: "precio_asc", label: "Precio: de menor a mayor" },
  { value: "precio_desc", label: "Precio: de mayor a menor" },
];

/**
 * Catálogo público de obras y servicios.
 *
 * Es la pantalla que conecta la galería con el backend: filtra y pagina
 * contra la API, y permite a un cliente autenticado armar su pedido.
 */
function Catalogo() {
  const { token, esCliente, autenticado } = useAuth();
  const toast = useToast();

  const [pagina, setPagina] = useState(1);
  const [buscar, setBuscar] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [artista, setArtista] = useState("");
  const [orden, setOrden] = useState("");
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(false);
  const [comprando, setComprando] = useState(null);

  const obras = useRecurso(
    (signal) =>
      api.listarObras(
        {
          page: pagina,
          page_size: TAMANO_PAGINA,
          buscar: busquedaAplicada || undefined,
          artista: artista || undefined,
          disponible: true,
        },
        signal
      ),
    [pagina, busquedaAplicada, artista]
  );

  const servicios = useRecurso(
    (signal) => api.listarServicios({ activo: true, page_size: 20 }, signal),
    []
  );

  function aplicarBusqueda(evento) {
    evento.preventDefault();
    setPagina(1);
    setBusquedaAplicada(buscar.trim());
  }

  function limpiarFiltros() {
    setBuscar("");
    setBusquedaAplicada("");
    setArtista("");
    setOrden("");
    setPagina(1);
  }

  async function pedir(item, tipo) {
    if (!autenticado) {
      toast.info("Inicia sesión para poder hacer un pedido.");
      return;
    }
    if (!esCliente) {
      toast.aviso("Solo las cuentas de cliente pueden hacer pedidos desde el catálogo.");
      return;
    }

    const clave = `${tipo}-${item.id}`;
    setComprando(clave);
    try {
      const detalle = tipo === "obra" ? { obra_id: item.id } : { servicio_id: item.id };
      await api.crearPedido([{ ...detalle, cantidad: 1 }], token);
      toast.exito(
        `Añadido a un pedido nuevo. Revísalo en «Mi cuenta» para confirmarlo.`
      );
      obras.recargar();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setComprando(null);
    }
  }

  // Los artistas se sacan de lo que ya devolvió la API, sin llamada extra.
  const artistas = [...new Set((obras.datos?.items ?? []).map((o) => o.artista))].sort();

  let listaObras = obras.datos?.items ?? [];
  if (orden === "precio_asc") listaObras = [...listaObras].sort((a, b) => a.precio - b.precio);
  if (orden === "precio_desc") listaObras = [...listaObras].sort((a, b) => b.precio - a.precio);

  const hayFiltros = Boolean(busquedaAplicada || artista || orden);

  return (
    <div className="contenedor py-10 sm:py-14">
      <header className="mb-8">
        <span className="etiqueta text-sienna">Colección disponible</span>
        <h1 className="mt-2 font-display text-3xl sm:text-4xl">Catálogo</h1>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft sm:text-base">
          Todas las piezas son originales y se entregan con certificado de
          autenticidad. Añade obras y servicios a tu pedido y confírmalo desde tu panel.
        </p>
      </header>

      {/* Filtros: una sola fila sobre el contenido */}
      <div className="mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <form
            onSubmit={aplicarBusqueda}
            className="flex w-full min-w-0 flex-col items-stretch gap-2
                       sm:w-auto sm:flex-1 sm:flex-row sm:items-end"
          >
            <div className="min-w-0 flex-1">
              <Input
                label="Buscar"
                name="buscar"
                value={buscar}
                onChange={(evento) => setBuscar(evento.target.value)}
                placeholder="Título o descripción…"
                maxLength={80}
              />
            </div>
            <Button type="submit" iconoIzquierda={Search} className="sm:mb-5">
              Buscar
            </Button>
          </form>

          <Button
            variant="secundario"
            iconoIzquierda={Filter}
            onClick={() => setFiltrosAbiertos((v) => !v)}
            className="sm:hidden"
          >
            Filtros
          </Button>

          <div className={`${filtrosAbiertos ? "flex" : "hidden"} w-full gap-3 sm:flex sm:w-auto`}>
            <div className="min-w-[160px] flex-1">
              <Select
                label="Artista"
                name="artista"
                value={artista}
                onChange={(evento) => {
                  setArtista(evento.target.value);
                  setPagina(1);
                }}
                options={[
                  { value: "", label: "Todos los artistas" },
                  ...artistas.map((a) => ({ value: a, label: a })),
                ]}
              />
            </div>
            <div className="min-w-[180px] flex-1">
              <Select
                label="Ordenar por"
                name="orden"
                value={orden}
                onChange={(evento) => setOrden(evento.target.value)}
                options={ORDENES}
              />
            </div>
          </div>
        </div>

        {hayFiltros && (
          <button
            type="button"
            onClick={limpiarFiltros}
            className="mt-1 inline-flex items-center gap-1.5 etiqueta text-muted
                       transition-colors hover:text-error"
          >
            <X size={12} aria-hidden="true" />
            Quitar filtros
          </button>
        )}
      </div>

      {/* Obras */}
      <section className="mb-14">
        <h2 className="mb-4 flex items-center gap-2 font-display text-xl">
          <Brush size={18} className="text-gold" aria-hidden="true" />
          Obras
          {obras.datos && (
            <span className="font-mono text-sm font-normal text-muted">
              ({obras.datos.total})
            </span>
          )}
        </h2>

        {obras.cargando ? (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="tarjeta p-5">
                <SkeletonFilas filas={1} />
              </div>
            ))}
          </div>
        ) : obras.error ? (
          <Alert tipo="error" titulo="No se pudo cargar el catálogo">
            {obras.error.message}
            <button
              type="button"
              onClick={obras.recargar}
              className="ml-2 underline underline-offset-2"
            >
              Reintentar
            </button>
          </Alert>
        ) : listaObras.length === 0 ? (
          <EmptyState
            icono={Search}
            titulo="No encontramos obras con esos criterios"
            descripcion="Prueba a cambiar la búsqueda o a quitar los filtros aplicados."
            accion={
              hayFiltros && (
                <Button variant="secundario" onClick={limpiarFiltros}>
                  Quitar filtros
                </Button>
              )
            }
          />
        ) : (
          <>
            <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {listaObras.map((obra) => (
                <li
                  key={obra.id}
                  className="tarjeta flex flex-col overflow-hidden transition-shadow hover:shadow-media"
                >
                  <div className="flex items-center justify-center border-b border-line/60
                                  bg-gradient-to-br from-wall to-paper-dim py-10">
                    {obra.imagen_url ? (
                      <img
                        src={obra.imagen_url}
                        alt={`${obra.titulo}, de ${obra.artista}`}
                        loading="lazy"
                        className="h-28 w-28 rounded-lg object-cover shadow-media"
                      />
                    ) : (
                      <span className="flex h-20 w-20 items-center justify-center rounded-full
                                       border-2 border-gold/40 font-display text-2xl italic text-gold/70">
                        {obra.titulo.charAt(0)}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-1 flex-col p-5">
                    <h3 className="font-display text-base leading-snug">{obra.titulo}</h3>
                    <p className="mt-0.5 text-xs text-muted">
                      {obra.artista} · {obra.anio}
                    </p>
                    <p className="mt-1 etiqueta text-muted">{obra.tecnica}</p>
                    <p className="mt-3 line-clamp-3 flex-1 text-sm text-ink-soft">
                      {obra.descripcion}
                    </p>

                    <div className="mt-4 flex items-end justify-between gap-3 border-t border-line/60 pt-4">
                      <div>
                        <span className="font-mono text-base font-bold tabular-nums text-forest">
                          {formatoMoneda(obra.precio)}
                        </span>
                        {obra.stock <= 1 && (
                          <p className="mt-0.5 etiqueta text-sienna">Pieza única</p>
                        )}
                      </div>
                      <Button
                        size="sm"
                        iconoIzquierda={ShoppingBag}
                        cargando={comprando === `obra-${obra.id}`}
                        onClick={() => pedir(obra, "obra")}
                      >
                        Pedir
                      </Button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>

            <Pagination
              pagina={pagina}
              tamanoPagina={TAMANO_PAGINA}
              total={obras.datos.total}
              onCambiar={setPagina}
              className="mt-8"
            />
          </>
        )}
      </section>

      {/* Servicios */}
      <section>
        <h2 className="mb-4 font-display text-xl">Servicios de la galería</h2>

        {servicios.cargando ? (
          <SkeletonFilas filas={3} />
        ) : (servicios.datos?.items ?? []).length === 0 ? (
          <EmptyState titulo="Todavía no hay servicios publicados" />
        ) : (
          <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {servicios.datos.items.map((servicio) => (
              <li key={servicio.id} className="tarjeta flex flex-col p-5">
                <h3 className="font-display text-base">{servicio.nombre}</h3>
                <p className="mt-2 flex-1 text-sm text-ink-soft">{servicio.descripcion}</p>
                <div className="mt-4 flex items-center justify-between gap-3 border-t border-line/60 pt-4">
                  <span className="font-mono text-sm font-bold tabular-nums text-forest">
                    {formatoMoneda(servicio.precio)}
                  </span>
                  <Button
                    size="sm"
                    variant="secundario"
                    cargando={comprando === `servicio-${servicio.id}`}
                    onClick={() => pedir(servicio, "servicio")}
                  >
                    Añadir
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {!autenticado && (
        <Alert tipo="info" className="mt-10">
          <Link to="/login" className="font-semibold underline underline-offset-2">
            Inicia sesión o crea tu cuenta
          </Link>{" "}
          para poder hacer pedidos y consultar tus facturas.
        </Alert>
      )}
    </div>
  );
}

export default Catalogo;
