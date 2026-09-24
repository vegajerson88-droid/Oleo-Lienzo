import { useState } from "react";
import { Link } from "react-router-dom";
import { MailCheck, Send } from "lucide-react";

import Alert from "./ui/Alert";
import Button from "./ui/Button";
import Input from "./ui/Input";
import { api } from "../services/api";
import { validateField } from "../utils/validators";

/**
 * Recuperación de contraseña.
 *
 * Componente reutilizable e independiente del formulario de inicio de sesión:
 * se usa tanto embebido en la página de login como por separado.
 *
 * El backend responde siempre lo mismo exista o no la cuenta, de modo que
 * esta pantalla no permite averiguar qué correos están registrados.
 */
function RecoverPassword({ onVolver }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [tocado, setTocado] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  function alCambiar(evento) {
    const { value } = evento.target;
    setEmail(value);
    setTocado(true);
    setError(validateField("email", value));
    if (errorServidor) setErrorServidor("");
  }

  async function alEnviar(evento) {
    evento.preventDefault();
    const mensaje = validateField("email", email);
    setError(mensaje);
    setTocado(true);
    if (mensaje) return;

    setEnviando(true);
    setErrorServidor("");
    try {
      await api.recuperarPassword(email);
      setEnviado(true);
    } catch (fallo) {
      setErrorServidor(
        fallo.status === 429
          ? "Has hecho demasiadas solicitudes. Espera un minuto."
          : fallo.message
      );
    } finally {
      setEnviando(false);
    }
  }

  const enlaceVolver = onVolver ? (
    <button
      type="button"
      onClick={onVolver}
      className="etiqueta text-muted transition-colors hover:text-forest"
    >
      Volver a iniciar sesión
    </button>
  ) : (
    <Link to="/login" className="etiqueta text-muted transition-colors hover:text-forest">
      Volver a iniciar sesión
    </Link>
  );

  return (
    <div className="w-full max-w-md rounded-2xl border-t-4 border-gold bg-paper p-7
                    shadow-media sm:p-9">
      {enviado ? (
        <div className="text-center">
          <span className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full
                           border border-exito/30 bg-exito-suave text-exito">
            <MailCheck size={26} aria-hidden="true" />
          </span>
          <h2 className="font-display text-2xl">Revisa tu correo</h2>
          <p className="mb-7 mt-3 text-sm leading-relaxed text-ink-soft">
            Si <strong className="text-ink">{email}</strong> corresponde a una cuenta
            registrada, recibirás en unos minutos un mensaje con el enlace para
            crear una contraseña nueva.
          </p>
          <Button variant="secundario" className="w-full" onClick={onVolver}>
            Volver a iniciar sesión
          </Button>
        </div>
      ) : (
        <>
          <h2 className="font-display text-2xl">Recuperar contraseña</h2>
          <p className="mb-6 mt-2 text-sm text-ink-soft">
            Escribe el correo de tu cuenta y te enviaremos las instrucciones para
            restablecerla.
          </p>

          <form onSubmit={alEnviar} noValidate className="flex flex-col gap-4">
            <Input
              label="Correo electrónico"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={alCambiar}
              error={tocado ? error : ""}
              valido={tocado && !error && Boolean(email)}
              maxLength={80}
              required
            />

            {errorServidor && <Alert tipo="error">{errorServidor}</Alert>}

            <Button
              type="submit"
              size="lg"
              cargando={enviando}
              iconoIzquierda={Send}
              className="w-full"
            >
              Enviar instrucciones
            </Button>
          </form>

          <div className="mt-6 text-center">{enlaceVolver}</div>
        </>
      )}
    </div>
  );
}

export default RecoverPassword;
