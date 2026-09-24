import { useEffect, useState } from "react";
import { api } from "../../services/api";
import Button from "../../components/ui/Button";

function UsuariosManager({ token }) {
  const [usuarios, setUsuarios] = useState([]);
  const [error, setError] = useState("");

  async function cargar() {
    try {
      const data = await api.listarUsuarios(token, { page: 1, page_size: 50 });
      setUsuarios(data.items);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { cargar(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function toggleActivo(u) {
    try {
      await api.actualizarUsuario(u.id, { activo: !u.activo }, token);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="bg-paper border border-ink/10 rounded-lg p-5">
      <h3 className="font-display text-lg mb-3">Usuarios ({usuarios.length})</h3>
      {error && <p className="text-sm text-sienna mb-3">{error}</p>}
      <ul className="flex flex-col gap-3">
        {usuarios.map((u) => (
          <li key={u.id} className="flex items-center justify-between gap-3 border-b border-ink/10 pb-2">
            <div>
              <p className="text-sm font-medium">{u.nombre} {u.apellido} — {u.email}</p>
              <p className="text-xs text-ink/60">
                Rol: {u.rol.nombre} · {u.activo ? "Activo" : "Inactivo"}
              </p>
            </div>
            <Button variant="ghost" className="!px-3 !py-1.5" onClick={() => toggleActivo(u)}>
              {u.activo ? "Desactivar" : "Activar"}
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default UsuariosManager;
