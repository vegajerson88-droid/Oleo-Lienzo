import { useEffect, useState } from "react";
import { api } from "../../services/api";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";

const vacio = { nombre: "", descripcion: "", precio: "" };

function ServiciosManager({ token, puedeEliminar }) {
  const [servicios, setServicios] = useState([]);
  const [error, setError] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [form, setForm] = useState(vacio);

  async function cargar() {
    try {
      const data = await api.listarServicios({ page: 1, page_size: 50 });
      setServicios(data.items);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { cargar(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  function editar(s) {
    setEditandoId(s.id);
    setForm({ nombre: s.nombre, descripcion: s.descripcion, precio: s.precio });
  }

  function cancelar() {
    setEditandoId(null);
    setForm(vacio);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const payload = { nombre: form.nombre, descripcion: form.descripcion, precio: Number(form.precio) };
    try {
      if (editandoId) await api.actualizarServicio(editandoId, payload, token);
      else await api.crearServicio(payload, token);
      cancelar();
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function eliminar(id) {
    if (!confirm("¿Eliminar este servicio?")) return;
    try {
      await api.eliminarServicio(id, token);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <form onSubmit={handleSubmit} className="bg-paper border border-ink/10 rounded-lg p-5 flex flex-col gap-3">
        <h3 className="font-display text-lg">{editandoId ? "Editar servicio" : "Nuevo servicio"}</h3>
        <Input label="Nombre" name="nombre" value={form.nombre} onChange={handleChange} required />
        <Input label="Precio (COP)" name="precio" type="number" value={form.precio} onChange={handleChange} required />
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
          <Button type="submit">{editandoId ? "Guardar cambios" : "Crear servicio"}</Button>
          {editandoId && <Button type="button" variant="ghost" onClick={cancelar}>Cancelar</Button>}
        </div>
      </form>

      <div className="bg-paper border border-ink/10 rounded-lg p-5">
        <h3 className="font-display text-lg mb-3">Servicios ({servicios.length})</h3>
        <ul className="flex flex-col gap-3">
          {servicios.map((s) => (
            <li key={s.id} className="flex items-center justify-between gap-3 border-b border-ink/10 pb-2">
              <div>
                <p className="text-sm font-medium">{s.nombre}</p>
                <p className="text-xs text-ink/60">${Number(s.precio).toLocaleString("es-CO")}</p>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button variant="ghost" className="!px-3 !py-1.5" onClick={() => editar(s)}>Editar</Button>
                {puedeEliminar && (
                  <Button variant="ghost" className="!px-3 !py-1.5 text-sienna" onClick={() => eliminar(s.id)}>
                    Eliminar
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default ServiciosManager;
