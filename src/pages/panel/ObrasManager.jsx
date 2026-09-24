import { useEffect, useState } from "react";
import { api, ApiError } from "../../services/api";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";

const vacio = {
  titulo: "", artista: "", anio: "", tecnica: "", precio: "", descripcion: "", imagen_url: "",
};

function ObrasManager({ token, puedeEliminar }) {
  const [obras, setObras] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [form, setForm] = useState(vacio);
  const [sugerencia, setSugerencia] = useState(null);
  const pageSize = 5;

  async function cargar() {
    setCargando(true);
    setError("");
    try {
      const data = await api.listarObras({ page, page_size: pageSize });
      setObras(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { cargar(); }, [page]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  function editar(obra) {
    setEditandoId(obra.id);
    setForm({
      titulo: obra.titulo, artista: obra.artista, anio: obra.anio, tecnica: obra.tecnica,
      precio: obra.precio, descripcion: obra.descripcion, imagen_url: obra.imagen_url || "",
    });
    setSugerencia(null);
  }

  function cancelarEdicion() {
    setEditandoId(null);
    setForm(vacio);
    setSugerencia(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const payload = {
      titulo: form.titulo,
      artista: form.artista,
      anio: Number(form.anio),
      tecnica: form.tecnica,
      precio: Number(form.precio),
      descripcion: form.descripcion,
      imagen_url: form.imagen_url || null,
    };
    try {
      if (editandoId) {
        await api.actualizarObra(editandoId, payload, token);
      } else {
        await api.crearObra(payload, token);
      }
      cancelarEdicion();
      cargar();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar la obra.");
    }
  }

  async function eliminar(id) {
    if (!confirm("¿Eliminar esta obra?")) return;
    try {
      await api.eliminarObra(id, token);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function pedirSugerenciaPrecio() {
    if (!form.anio || !form.tecnica) return;
    try {
      const data = await api.precioSugerido(Number(form.anio), form.tecnica, token);
      setSugerencia(data);
    } catch (err) {
      setSugerencia({ disponible: false, detalle: err.message });
    }
  }

  const totalPaginas = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <form onSubmit={handleSubmit} className="bg-paper border border-ink/10 rounded-lg p-5 flex flex-col gap-3">
        <h3 className="font-display text-lg">{editandoId ? "Editar obra" : "Nueva obra"}</h3>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Título" name="titulo" value={form.titulo} onChange={handleChange} required />
          <Input label="Artista" name="artista" value={form.artista} onChange={handleChange} required />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Año" name="anio" type="number" value={form.anio} onChange={handleChange} required />
          <Input label="Técnica" name="tecnica" value={form.tecnica} onChange={handleChange} required />
        </div>
        <div className="grid grid-cols-2 gap-3 items-end">
          <Input label="Precio (COP)" name="precio" type="number" value={form.precio} onChange={handleChange} required />
          <Button type="button" variant="outline" onClick={pedirSugerenciaPrecio}>
            Sugerir precio (IA)
          </Button>
        </div>
        {sugerencia && (
          <p className="text-xs text-ink/70 bg-gold/10 border border-gold/30 rounded-md px-3 py-2">
            {sugerencia.disponible
              ? `Precio estimado por IA: $${sugerencia.precio_estimado.toLocaleString("es-CO")} (modelo ${sugerencia.version_modelo}, variables: ${sugerencia.variables_utilizadas.join(", ")})`
              : sugerencia.detalle}
          </p>
        )}
        <Input label="URL de imagen (opcional)" name="imagen_url" value={form.imagen_url} onChange={handleChange} />
        <label className="flex flex-col gap-1.5">
          <span className="font-mono text-xs uppercase tracking-wider text-ink/80">Descripción</span>
          <textarea
            name="descripcion"
            value={form.descripcion}
            onChange={handleChange}
            required
            rows={3}
            className="rounded-md border border-ink/20 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gold/60"
          />
        </label>
        {error && <p className="text-sm text-sienna">{error}</p>}
        <div className="flex gap-3">
          <Button type="submit">{editandoId ? "Guardar cambios" : "Crear obra"}</Button>
          {editandoId && (
            <Button type="button" variant="ghost" onClick={cancelarEdicion}>Cancelar</Button>
          )}
        </div>
      </form>

      <div className="bg-paper border border-ink/10 rounded-lg p-5">
        <h3 className="font-display text-lg mb-3">Obras ({total})</h3>
        {cargando ? (
          <p className="text-sm text-ink/60">Cargando...</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {obras.map((o) => (
              <li key={o.id} className="flex items-center justify-between gap-3 border-b border-ink/10 pb-2">
                <div>
                  <p className="text-sm font-medium">{o.titulo} — {o.artista} ({o.anio})</p>
                  <p className="text-xs text-ink/60">{o.tecnica} · ${Number(o.precio).toLocaleString("es-CO")}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button variant="ghost" className="!px-3 !py-1.5" onClick={() => editar(o)}>Editar</Button>
                  {puedeEliminar && (
                    <Button variant="ghost" className="!px-3 !py-1.5 text-sienna" onClick={() => eliminar(o.id)}>
                      Eliminar
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
        <div className="flex items-center justify-between mt-4 text-xs font-mono uppercase tracking-wider">
          <Button variant="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Anterior</Button>
          <span>Página {page} de {totalPaginas}</span>
          <Button variant="ghost" disabled={page >= totalPaginas} onClick={() => setPage((p) => p + 1)}>Siguiente</Button>
        </div>
      </div>
    </div>
  );
}

export default ObrasManager;
