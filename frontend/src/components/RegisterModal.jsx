import { useEffect, useState } from "react";
import { CheckCircle2, UserPlus } from "lucide-react";

import Modal from "./ui/Modal";
import Alert from "./ui/Alert";
import Button from "./ui/Button";
import Input from "./ui/Input";
import Select from "./ui/Select";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { validateField, validateForm } from "../utils/validators";

const CAMPOS = [
  "nombre", "apellido", "tipoDocumento", "numeroDocumento",
  "direccion", "telefono", "email", "password", "confirmarPassword",
];

const VALORES_INICIALES = Object.fromEntries(CAMPOS.map((campo) => [campo, ""]));

const TIPOS_DOCUMENTO = [
  { value: "", label: "Selecciona…" },
  { value: "CC", label: "Cédula de ciudadanía" },
  { value: "CE", label: "Cédula de extranjería" },
  { value: "TI", label: "Tarjeta de identidad" },
  { value: "PA", label: "Pasaporte" },
];

/** Campos que solo aceptan dígitos, filtrados mientras se escribe. */
const SOLO_DIGITOS = new Set(["numeroDocumento", "telefono"]);

/**
 * Registro de clientes en una ventana modal.
 *
 * Valida en tiempo real mientras el usuario escribe y vuelve a validar el
 * formulario completo al enviarlo. Estas comprobaciones son de comodidad: el
 * backend repite todas por su cuenta y es quien decide.
 */
function RegisterModal({ isOpen, onClose, onSuccess }) {
  const { registrar } = useAuth();
  const toast = useToast();

  const [valores, setValores] = useState(VALORES_INICIALES);
  const [errores, setErrores] = useState({});
  const [tocados, setTocados] = useState({});
  const [registrado, setRegistrado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  // Cada apertura empieza en limpio.
  useEffect(() => {
    if (!isOpen) return;
    setValores(VALORES_INICIALES);
    setErrores({});
    setTocados({});
    setRegistrado(false);
    setErrorServidor("");
  }, [isOpen]);

  function alCambiar(evento) {
    const { name } = evento.target;
    let { value } = evento.target;

    // Impide teclear letras donde solo caben números.
    if (SOLO_DIGITOS.has(name)) value = value.replace(/\D/g, "");

    const siguiente = { ...valores, [name]: value };
    setValores(siguiente);
    setTocados((previos) => ({ ...previos, [name]: true }));
    setErrores((previos) => ({
      ...previos,
      [name]: validateField(name, value, siguiente),
      // Al cambiar la contraseña hay que revalidar su confirmación.
      ...(name === "password"
        ? {
            confirmarPassword: validateField(
              "confirmarPassword", siguiente.confirmarPassword, siguiente
            ),
          }
        : {}),
    }));
    if (errorServidor) setErrorServidor("");
  }

  async function alEnviar(evento) {
    evento.preventDefault();

    const encontrados = validateForm(valores, CAMPOS);
    setErrores(encontrados);
    setTocados(Object.fromEntries(CAMPOS.map((campo) => [campo, true])));
    if (Object.keys(encontrados).length > 0) {
      setErrorServidor("Revisa los campos marcados antes de continuar.");
      return;
    }

    setEnviando(true);
    setErrorServidor("");
    try {
      await registrar({
        nombre: valores.nombre,
        apellido: valores.apellido,
        tipo_documento: valores.tipoDocumento,
        numero_documento: valores.numeroDocumento,
        direccion: valores.direccion,
        telefono: valores.telefono,
        email: valores.email,
        password: valores.password,
        confirmar_password: valores.confirmarPassword,
      });
      setRegistrado(true);
      toast.exito("Cuenta creada. Ya puedes iniciar sesión.");
      onSuccess?.(valores);
    } catch (error) {
      setErrorServidor(
        error.esConflicto
          ? "Ya existe una cuenta con ese correo o ese número de documento."
          : error.message
      );
    } finally {
      setEnviando(false);
    }
  }

  const campoValido = (campo) => tocados[campo] && !errores[campo] && Boolean(valores[campo]);

  return (
    <Modal
      abierto={isOpen}
      onCerrar={onClose}
      titulo={registrado ? "¡Registro completado!" : "Crear una cuenta"}
      descripcion={
        registrado ? undefined : "Todos los campos son obligatorios."
      }
      ancho="lg"
      pie={
        registrado ? (
          <Button onClick={onClose}>Ir a iniciar sesión</Button>
        ) : (
          <>
            <Button variant="fantasma" onClick={onClose} disabled={enviando}>
              Cancelar
            </Button>
            <Button
              type="submit"
              form="formulario-registro"
              cargando={enviando}
              iconoIzquierda={UserPlus}
            >
              {enviando ? "Creando la cuenta…" : "Registrarme"}
            </Button>
          </>
        )
      }
    >
      {registrado ? (
        <div className="py-6 text-center">
          <span className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full
                           border border-exito/30 bg-exito-suave text-exito">
            <CheckCircle2 size={26} aria-hidden="true" />
          </span>
          <p className="font-display text-lg">Hola, {valores.nombre}</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
            Tu cuenta quedó creada correctamente y te enviamos un correo de
            bienvenida. Ya puedes iniciar sesión con {valores.email}.
          </p>
        </div>
      ) : (
        <form id="formulario-registro" onSubmit={alEnviar} noValidate className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Nombre" name="nombre" autoComplete="given-name"
              value={valores.nombre} onChange={alCambiar}
              error={tocados.nombre ? errores.nombre : ""} valido={campoValido("nombre")}
              maxLength={40} required
            />
            <Input
              label="Apellido" name="apellido" autoComplete="family-name"
              value={valores.apellido} onChange={alCambiar}
              error={tocados.apellido ? errores.apellido : ""} valido={campoValido("apellido")}
              maxLength={40} required
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Tipo de documento" name="tipoDocumento"
              value={valores.tipoDocumento} onChange={alCambiar}
              error={tocados.tipoDocumento ? errores.tipoDocumento : ""}
              options={TIPOS_DOCUMENTO} required
            />
            <Input
              label="Número de documento" name="numeroDocumento"
              inputMode="numeric" value={valores.numeroDocumento} onChange={alCambiar}
              error={tocados.numeroDocumento ? errores.numeroDocumento : ""}
              valido={campoValido("numeroDocumento")}
              hint="Entre 6 y 15 dígitos." maxLength={15} contador required
            />
          </div>

          <Input
            label="Dirección" name="direccion" autoComplete="street-address"
            value={valores.direccion} onChange={alCambiar}
            error={tocados.direccion ? errores.direccion : ""} valido={campoValido("direccion")}
            maxLength={100} contador required
          />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Teléfono" name="telefono" inputMode="numeric" autoComplete="tel"
              value={valores.telefono} onChange={alCambiar}
              error={tocados.telefono ? errores.telefono : ""} valido={campoValido("telefono")}
              hint="Entre 7 y 10 dígitos." maxLength={10} contador required
            />
            <Input
              label="Correo electrónico" name="email" type="email" autoComplete="email"
              value={valores.email} onChange={alCambiar}
              error={tocados.email ? errores.email : ""} valido={campoValido("email")}
              maxLength={80} required
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Contraseña" name="password" type="password" autoComplete="new-password"
              value={valores.password} onChange={alCambiar}
              error={tocados.password ? errores.password : ""}
              hint="Mín. 8 caracteres, mayúscula, minúscula y número."
              maxLength={64} required
            />
            <Input
              label="Confirmar contraseña" name="confirmarPassword" type="password"
              autoComplete="new-password"
              value={valores.confirmarPassword} onChange={alCambiar}
              error={tocados.confirmarPassword ? errores.confirmarPassword : ""}
              valido={campoValido("confirmarPassword")}
              maxLength={64} required
            />
          </div>

          {errorServidor && <Alert tipo="error">{errorServidor}</Alert>}
        </form>
      )}
    </Modal>
  );
}

export default RegisterModal;
