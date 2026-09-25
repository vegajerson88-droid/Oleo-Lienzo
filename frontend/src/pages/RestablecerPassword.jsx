import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { KeyRound } from "lucide-react";

import Logo from "../components/Logo";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { useToast } from "../context/ToastContext";
import { api } from "../services/api";
import { validateField } from "../utils/validators";

/**
 * Pantalla a la que lleva el enlace del correo de recuperación.
 *
 * El token viaja en la URL (?token=...) y lo verifica el backend: aquí solo
 * se comprueba que la contraseña nueva cumple la política y coincide.
 */
function RestablecerPassword() {
  const [parametros] = useSearchParams();
  const navegar = useNavigate();
  const toast = useToast();
  const token = parametros.get("token") ?? "";

  const [valores, setValores] = useState({ password: "", confirmarPassword: "" });
  const [errores, setErrores] = useState({});
  const [tocados, setTocados] = useState({});
  const [enviando, setEnviando] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  function alCambiar(evento) {
    const { name, value } = evento.target;
    const siguiente = { ...valores, [name]: value };
    setValores(siguiente);
    setTocados((previos) => ({ ...previos, [name]: true }));
    setErrores((previos) => ({
      ...previos,
      [name]: validateField(name, value, siguiente),
      ...(name === "password"
        ? {
            confirmarPassword: validateField(
              "confirmarPassword",
              siguiente.confirmarPassword,
              siguiente
            ),
          }
        : {}),
    }));
    if (errorServidor) setErrorServidor("");
  }

  async function alEnviar(evento) {
    evento.preventDefault();

    const encontrados = {
      password: validateField("password", valores.password, valores),
      confirmarPassword: validateField("confirmarPassword", valores.confirmarPassword, valores),
    };
    setErrores(encontrados);
    setTocados({ password: true, confirmarPassword: true });
    if (encontrados.password || encontrados.confirmarPassword) return;

    setEnviando(true);
    setErrorServidor("");
    try {
      await api.restablecerPassword(token, valores.password, valores.confirmarPassword);
      toast.exito("Tu contraseña se actualizó. Ya puedes iniciar sesión.");
      navegar("/login", { replace: true });
    } catch (error) {
      setErrorServidor(error.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-wall">
      <div className="border-b-[3px] border-gold bg-forest py-6">
        <div className="contenedor flex justify-center">
          <Link to="/" aria-label="Óleo & Lienzo, ir al inicio">
            <Logo tamano="md" />
          </Link>
        </div>
      </div>

      <div className="flex flex-1 items-center justify-center px-4 py-12 sm:px-6">
        <div className="w-full max-w-md rounded-2xl border-t-4 border-gold bg-paper p-7
                        shadow-media sm:p-9">
          <h1 className="font-display text-2xl">Crear una contraseña nueva</h1>
          <p className="mb-6 mt-2 text-sm text-ink-soft">
            Elige una contraseña segura para tu cuenta.
          </p>

          {!token ? (
            <Alert tipo="error" titulo="Enlace incompleto">
              Este enlace no incluye el código de recuperación. Solicita uno nuevo desde
              «¿Olvidaste tu contraseña?».
            </Alert>
          ) : (
            <form onSubmit={alEnviar} noValidate className="flex flex-col gap-4">
              <Input
                label="Contraseña nueva"
                name="password"
                type="password"
                autoComplete="new-password"
                value={valores.password}
                onChange={alCambiar}
                error={tocados.password ? errores.password : ""}
                hint="Mínimo 8 caracteres, con mayúscula, minúscula y número."
                maxLength={64}
                required
              />
              <Input
                label="Repite la contraseña"
                name="confirmarPassword"
                type="password"
                autoComplete="new-password"
                value={valores.confirmarPassword}
                onChange={alCambiar}
                error={tocados.confirmarPassword ? errores.confirmarPassword : ""}
                valido={
                  tocados.confirmarPassword &&
                  !errores.confirmarPassword &&
                  Boolean(valores.confirmarPassword)
                }
                maxLength={64}
                required
              />

              {errorServidor && <Alert tipo="error">{errorServidor}</Alert>}

              <Button
                type="submit"
                size="lg"
                cargando={enviando}
                iconoIzquierda={KeyRound}
                className="mt-1 w-full"
              >
                Guardar la contraseña
              </Button>
            </form>
          )}

          <Link
            to="/login"
            className="mt-6 block text-center etiqueta text-muted transition-colors hover:text-forest"
          >
            Volver a iniciar sesión
          </Link>
        </div>
      </div>
    </div>
  );
}

export default RestablecerPassword;
