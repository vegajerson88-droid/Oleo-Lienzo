import { useState } from "react";
import { Pencil, Plus, Power, Search, Trash2, Users } from "lucide-react";

import Alert from "../../components/ui/Alert";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import Pagination from "../../components/ui/Pagination";
import Select from "../../components/ui/Select";
import { SkeletonFilas } from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { useRecurso } from "../../hooks/useRecurso";
import { api } from "../../services/api";
import { validateForm } from "../../utils/validators";

const TAMANO_PAGINA = 10;

const FILTRO_ROLES = [
  { value: "", label: "Todos los roles" },
  { value: "administrador", label: "Administradores" },
  { value: "empleado", label: "Empleados" },
  { value: "cliente", label: "Clientes" },
];

const TIPOS_DOCUMENTO = [
  { value: "CC", label: "Cédula de ciudadanía" },
  { value: "CE", label: "Cédula de extranjería" },
  { value: "TI", label: "Tarjeta de identidad" },
  { value: "PA", label: "Pasaporte" },
];

const CAMPOS_ALTA = [
  "nombre", "apellido", "numeroDocumento", "direccion",
  "telefono", "email", "password", "confirmarPassword",
];
const CAMPOS_EDICION = ["nombre", "apellido", "direccion", "telefono"];

const VACIO = {
  nombre: "", apellido: "", tipoDocumento: "CC", numeroDocumento: "",
  direccion: "", telefono: "", email: "",
  password: "", confirmarPassword: "", rolNombre: "cliente",
};

/** Gestión completa de usuarios. Reservada al administrador. */
function UsuariosManager({ token }) {
  const toast = useToast();
  const { usuario: yo } = useAuth();

  const [pagina, setPagina] = useState(1);
  const [rol, setRol] = useState("");
  const [buscar, setBuscar] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");

  const [modalAbierto, setModalAbierto] = useState(false);
  const [editando, setEditando] = useState(null);
  const [formulario, setFormulario] = useState(VACIO);
  const [errores, setErrores] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [errorFormulario, setErrorFormulario] = useState("");
  const [cambiandoEstado, setCambiandoEstado] = useState(null);
  const [aEliminar, setAEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);

  const usuarios = useRecurso(
    (signal) =>
      api.listarUsuarios(
        token,
        {
          page: pagina, page_size: TAMANO_PAGINA,
          rol: rol || undefined, buscar: busquedaAplicada || undefined,
        },
        signal
      ),
    [pagina, rol, busquedaAplicada]
  );

  const roles = useRecurso((signal) => api.listarRoles(token, signal), []);

  function abrirAlta() {
    setEditando(null);
    setFormulario(VACIO);
    setErrores({});
    setErrorFormulario("");
    setModalAbierto(true);
  }

  function abrirEdicion(usuario) {
    setEditando(usuario);
    setFormulario({
      ...VACIO,
      nombre: usuario.nombre, apellido: usuario.apellido,
      tipoDocumento: usuario.tipo_documento, numeroDocumento: usuario.numero_documento,
      direccion: usuario.direccion, telefono: usuario.telefono, email: usuario.email,
      rolNombre: usuario.rol.nombre,
    });
    setErrores({});
    setErrorFormulario("");
    setModalAbierto(true);
  }

  function alCambiar(evento) {
    const { name } = evento.target;
    let { value } = evento.target;
    if (name === "numeroDocumento" || name === "telefono") value = value.replace(/\D/g, "");
    setFormulario((previo) => ({ ...previo, [name]: value }));
    setErrores((previos) => ({ ...previos, [name]: undefined }));
    if (errorFormulario) setErrorFormulario("");
  }

  async function guardar(evento) {
    evento.preventDefault();

    const campos = editando ? CAMPOS_EDICION : CAMPOS_ALTA;
    const encontrados = validateForm(formulario, campos);
    setErrores(encontrados);
    if (Object.keys(encontrados).length > 0) {
      setErrorFormulario("Revisa los campos marcados.");
      return;
    }

    setGuardando(true);
    setErrorFormulario("");
    try {
      if (editando) {
        const rolDestino = (roles.datos ?? []).find((r) => r.nombre === formulario.rolNombre);
        // PUT: el formulario trae todos los campos modificables del usuario.
        await api.reemplazarUsuario(
          editando.id,
          {
            nombre: formulario.nombre.trim(),
            apellido: formulario.apellido.trim(),
            direccion: formulario.direccion.trim(),
            telefono: formulario.telefono,
            rol_id: rolDestino?.id ?? editando.rol.id,
            activo: editando.activo,
          },
          token
        );
        toast.exito(`${formulario.nombre} se actualizó.`);
      } else {
        await api.crearUsuario(
          {
            nombre: formulario.nombre.trim(),
            apellido: formulario.apellido.trim(),
            tipo_documento: formulario.tipoDocumento,
            numero_documento: formulario.numeroDocumento,
            direccion: formulario.direccion.trim(),
            telefono: formulario.telefono,
            email: formulario.email.trim(),
            password: formulario.password,
            confirmar_password: formulario.confirmarPassword,
            rol_nombre: formulario.rolNombre,
          },
          token
        );
        toast.exito(`Cuenta de ${formulario.nombre} creada como ${formulario.rolNombre}.`);
      }
      setModalAbierto(false);
      usuarios.recargar();
    } catch (error) {
      setErrorFormulario(
        error.esConflicto
          ? "Ya existe un usuario con ese correo o número de documento."
          : error.message
      );
    } finally {
      setGuardando(false);
    }
  }

  async function alternarEstado(usuario) {
    setCambiandoEstado(usuario.id);
    try {
      await api.cambiarEstadoUsuario(usuario.id, !usuario.activo, token);
      toast.exito(
        `${usuario.nombre} quedó ${!usuario.activo ? "activo" : "inactivo"}.`
      );
      usuarios.recargar();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setCambiandoEstado(null);
    }
  }

  async function confirmarEliminacion() {
    setEliminando(true);
    try {
      await api.eliminarUsuario(aEliminar.id, token);
      toast.exito(`${aEliminar.nombre} se eliminó del sistema.`);
      setAEliminar(null);
      usuarios.recargar();
    } catch (error) {
      toast.error(
        error.esConflicto
          ? "No se puede eliminar: tiene pedidos, ventas o facturas. Desactívalo en su lugar."
          : error.message
      );
    } finally {
      setEliminando(false);
    }
  }

  const columnas = [
    {
      clave: "nombre", titulo: "Usuario",
      render: (u) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-ink">
            {u.nombre} {u.apellido}
            {u.id === yo?.id && <span className="ml-2 etiqueta text-gold">tú</span>}
          </p>
          <p className="truncate text-xs text-muted">{u.email}</p>
        </div>
      ),
    },
    {
      clave: "documento", titulo: "Documento",
      render: (u) => (
        <span className="font-mono text-xs">
          {u.tipo_documento} {u.numero_documento}
        </span>
      ),
    },
    {
      clave: "rol", titulo: "Rol", alinear: "centro",
      render: (u) => <Badge estado={u.rol.nombre} />,
    },
    {
      clave: "activo", titulo: "Estado", alinear: "centro",
      render: (u) => <Badge estado={u.activo ? "activo" : "inactivo"} />,
    },
    {
      clave: "acciones", titulo: "Acciones", alinear: "derecha",
      render: (u) => (
        <div className="flex flex-wrap justify-end gap-1.5">
          <Button size="sm" variant="fantasma" iconoIzquierda={Pencil} onClick={() => abrirEdicion(u)}>
            Editar
          </Button>
          <Button
            size="sm" variant="fantasma" iconoIzquierda={Power}
            cargando={cambiandoEstado === u.id}
            disabled={u.id === yo?.id}
            title={u.id === yo?.id ? "No puedes desactivar tu propia cuenta" : undefined}
            onClick={() => alternarEstado(u)}
          >
            {u.activo ? "Desactivar" : "Activar"}
          </Button>
          <Button
            size="sm" variant="fantasma" iconoIzquierda={Trash2}
            className="text-error hover:bg-error/10"
            disabled={u.id === yo?.id}
            onClick={() => setAEliminar(u)}
          >
            Borrar
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <Card
        titulo={`Usuarios${usuarios.datos ? ` (${usuarios.datos.total})` : ""}`}
        descripcion="Alta, edición, cambio de estado y eliminación de cuentas."
        icono={Users}
        acciones={
          <Button size="sm" iconoIzquierda={Plus} onClick={abrirAlta}>
            Nuevo usuario
          </Button>
        }
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
              placeholder="Nombre, correo o documento…" maxLength={80}
            />
          </div>
          <div className="min-w-[170px]">
            <Select
              label="Rol" name="rol" value={rol} options={FILTRO_ROLES}
              onChange={(evento) => {
                setRol(evento.target.value);
                setPagina(1);
              }}
            />
          </div>
          <Button type="submit" iconoIzquierda={Search} className="mb-5">
            Buscar
          </Button>
        </form>

        {usuarios.cargando ? (
          <SkeletonFilas filas={5} />
        ) : usuarios.error ? (
          <Alert tipo="error">{usuarios.error.message}</Alert>
        ) : usuarios.datos.items.length === 0 ? (
          <EmptyState icono={Users} titulo="Ningún usuario coincide con la búsqueda" />
        ) : (
          <>
            <Table columnas={columnas} filas={usuarios.datos.items} claveFila={(u) => u.id} />
            <Pagination
              pagina={pagina} tamanoPagina={TAMANO_PAGINA}
              total={usuarios.datos.total} onCambiar={setPagina} className="mt-5"
            />
          </>
        )}
      </Card>

      <Modal
        abierto={modalAbierto}
        onCerrar={() => setModalAbierto(false)}
        titulo={editando ? `Editar a ${editando.nombre} ${editando.apellido}` : "Nuevo usuario"}
        descripcion={
          editando
            ? "El correo y el documento no se pueden cambiar: identifican la cuenta."
            : "La contraseña se guarda cifrada; nadie puede recuperarla en claro."
        }
        ancho="lg"
        pie={
          <>
            <Button variant="fantasma" onClick={() => setModalAbierto(false)} disabled={guardando}>
              Cancelar
            </Button>
            <Button type="submit" form="formulario-usuario" cargando={guardando}>
              {editando ? "Guardar cambios" : "Crear usuario"}
            </Button>
          </>
        }
      >
        <form id="formulario-usuario" onSubmit={guardar} noValidate className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Nombre" name="nombre" value={formulario.nombre} onChange={alCambiar}
                   error={errores.nombre} maxLength={40} required />
            <Input label="Apellido" name="apellido" value={formulario.apellido} onChange={alCambiar}
                   error={errores.apellido} maxLength={40} required />
          </div>

          {!editando && (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Select label="Tipo de documento" name="tipoDocumento"
                        value={formulario.tipoDocumento} onChange={alCambiar}
                        options={TIPOS_DOCUMENTO} required />
                <Input label="Número de documento" name="numeroDocumento" inputMode="numeric"
                       value={formulario.numeroDocumento} onChange={alCambiar}
                       error={errores.numeroDocumento} maxLength={15} contador required />
              </div>
              <Input label="Correo electrónico" name="email" type="email"
                     value={formulario.email} onChange={alCambiar}
                     error={errores.email} maxLength={80} required />
            </>
          )}

          <Input label="Dirección" name="direccion" value={formulario.direccion} onChange={alCambiar}
                 error={errores.direccion} maxLength={100} required />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Teléfono" name="telefono" inputMode="numeric"
                   value={formulario.telefono} onChange={alCambiar}
                   error={errores.telefono} maxLength={10} required />
            <Select
              label="Rol" name="rolNombre" value={formulario.rolNombre} onChange={alCambiar}
              options={(roles.datos ?? []).map((r) => ({
                value: r.nombre,
                label: r.nombre.charAt(0).toUpperCase() + r.nombre.slice(1),
              }))}
              hint={editando ? "Cambiar el rol cambia a qué panel accede." : undefined}
              required
            />
          </div>

          {!editando && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input label="Contraseña" name="password" type="password"
                     value={formulario.password} onChange={alCambiar}
                     error={errores.password}
                     hint="Mín. 8 caracteres, mayúscula, minúscula y número."
                     maxLength={64} required />
              <Input label="Confirmar contraseña" name="confirmarPassword" type="password"
                     value={formulario.confirmarPassword} onChange={alCambiar}
                     error={errores.confirmarPassword} maxLength={64} required />
            </div>
          )}

          {errorFormulario && <Alert tipo="error">{errorFormulario}</Alert>}
        </form>
      </Modal>

      <Modal
        abierto={Boolean(aEliminar)}
        onCerrar={() => setAEliminar(null)}
        titulo="Eliminar usuario"
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
          Vas a eliminar la cuenta de{" "}
          <strong className="text-ink">{aEliminar?.nombre} {aEliminar?.apellido}</strong>.
        </p>
        <Alert tipo="aviso" className="mt-4">
          Si tiene pedidos, ventas o facturas, el servidor rechazará el borrado
          para conservar el histórico. En ese caso, desactívalo con el botón
          «Desactivar»: no podrá iniciar sesión, pero sus registros se mantienen.
        </Alert>
      </Modal>
    </>
  );
}

export default UsuariosManager;
