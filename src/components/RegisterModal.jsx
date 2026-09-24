import { useState, useEffect } from "react";
import { X } from "lucide-react";
import Input from "./ui/Input";
import Select from "./ui/Select";
import Button from "./ui/Button";
import { validateField, validateForm } from "../utils/validators";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../services/api";

const FIELDS = [
  "nombre",
  "apellido",
  "tipoDocumento",
  "numeroDocumento",
  "direccion",
  "telefono",
  "email",
  "password",
  "confirmarPassword",
];

const initialValues = {
  nombre: "",
  apellido: "",
  tipoDocumento: "",
  numeroDocumento: "",
  direccion: "",
  telefono: "",
  email: "",
  password: "",
  confirmarPassword: "",
};

const tipoDocumentoOptions = [
  { value: "", label: "Selecciona..." },
  { value: "CC", label: "Cédula de ciudadanía" },
  { value: "CE", label: "Cédula de extranjería" },
  { value: "TI", label: "Tarjeta de identidad" },
  { value: "PA", label: "Pasaporte" },
];

function RegisterModal({ isOpen, onClose, onSuccess }) {
  const { registrar } = useAuth();
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [registrado, setRegistrado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  // Cierra con la tecla Escape y bloquea el scroll del body mientras está abierto
  useEffect(() => {
    if (!isOpen) return;
    document.body.style.overflow = "hidden";
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKey);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      setValues(initialValues);
      setErrors({});
      setTouched({});
      setRegistrado(false);
      setErrorServidor("");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    const next = { ...values, [name]: value };
    setValues(next);
    setTouched((prev) => ({ ...prev, [name]: true }));
    setErrors((prev) => ({
      ...prev,
      [name]: validateField(name, value, next),
      ...(name === "password"
        ? { confirmarPassword: validateField("confirmarPassword", next.confirmarPassword, next) }
        : {}),
    }));
    if (errorServidor) setErrorServidor("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const foundErrors = validateForm(values, FIELDS);
    setErrors(foundErrors);
    setTouched(FIELDS.reduce((acc, f) => ({ ...acc, [f]: true }), {}));
    if (Object.keys(foundErrors).length > 0) return;

    setEnviando(true);
    setErrorServidor("");
    try {
      await registrar({
        nombre: values.nombre,
        apellido: values.apellido,
        tipo_documento: values.tipoDocumento,
        numero_documento: values.numeroDocumento,
        direccion: values.direccion,
        telefono: values.telefono,
        email: values.email,
        password: values.password,
        confirmar_password: values.confirmarPassword,
      });
      setRegistrado(true);
      onSuccess?.(values);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setErrorServidor("Ya existe una cuenta con ese correo o número de documento.");
      } else {
        setErrorServidor(err.message || "No se pudo completar el registro.");
      }
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="register-modal-title"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-paper w-full max-w-lg rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10 sticky top-0 bg-paper rounded-t-xl">
          <h2 id="register-modal-title" className="font-display text-xl">
            Crear una cuenta
          </h2>
          <button
            onClick={onClose}
            aria-label="Cerrar"
            className="text-ink/60 hover:text-sienna transition-colors"
          >
            <X size={22} />
          </button>
        </div>

        {registrado ? (
          <div className="p-8 text-center">
            <p className="font-display text-lg text-forest mb-2">
              ¡Registro exitoso!
            </p>
            <p className="text-sm text-ink/70 mb-6">
              Hola {values.nombre}, tu cuenta fue creada correctamente. Ya
              puedes iniciar sesión con tu correo y contraseña.
            </p>
            <Button onClick={onClose}>Ir a iniciar sesión</Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate className="p-6 flex flex-col gap-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Nombre"
                name="nombre"
                value={values.nombre}
                onChange={handleChange}
                error={touched.nombre && errors.nombre}
                maxLength={40}
              />
              <Input
                label="Apellido"
                name="apellido"
                value={values.apellido}
                onChange={handleChange}
                error={touched.apellido && errors.apellido}
                maxLength={40}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Tipo de documento"
                name="tipoDocumento"
                value={values.tipoDocumento}
                onChange={handleChange}
                error={touched.tipoDocumento && errors.tipoDocumento}
                options={tipoDocumentoOptions}
              />
              <Input
                label="Número de documento"
                name="numeroDocumento"
                inputMode="numeric"
                value={values.numeroDocumento}
                onChange={handleChange}
                error={touched.numeroDocumento && errors.numeroDocumento}
                maxLength={15}
              />
            </div>

            <Input
              label="Dirección"
              name="direccion"
              value={values.direccion}
              onChange={handleChange}
              error={touched.direccion && errors.direccion}
              maxLength={100}
            />

            <Input
              label="Teléfono"
              name="telefono"
              inputMode="numeric"
              value={values.telefono}
              onChange={handleChange}
              error={touched.telefono && errors.telefono}
              maxLength={10}
            />

            <Input
              label="Correo electrónico"
              name="email"
              type="email"
              value={values.email}
              onChange={handleChange}
              error={touched.email && errors.email}
              maxLength={80}
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Contraseña"
                name="password"
                type="password"
                value={values.password}
                onChange={handleChange}
                error={touched.password && errors.password}
                hint={!errors.password ? "Mín. 8 caracteres, mayúscula, minúscula y número." : undefined}
                maxLength={64}
              />
              <Input
                label="Confirmar contraseña"
                name="confirmarPassword"
                type="password"
                value={values.confirmarPassword}
                onChange={handleChange}
                error={touched.confirmarPassword && errors.confirmarPassword}
                maxLength={64}
              />
            </div>

            {errorServidor && (
              <p className="text-sm text-sienna bg-sienna/10 border border-sienna/30 rounded-md px-3 py-2">
                {errorServidor}
              </p>
            )}

            <div className="flex flex-col sm:flex-row gap-3 mt-2">
              <Button type="submit" className="flex-1" disabled={enviando}>
                {enviando ? "Registrando..." : "Registrarme"}
              </Button>
              <Button type="button" variant="outline" className="flex-1" onClick={onClose} disabled={enviando}>
                Cancelar
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default RegisterModal;
