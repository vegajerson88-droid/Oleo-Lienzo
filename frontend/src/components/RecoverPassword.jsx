import { useState } from "react";
import { Link } from "react-router-dom";
import { MailCheck, MailWarning, Send } from "lucide-react";

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
  // Qué respondió el servidor: si pudo enviar el correo y, en desarrollo
  // sin SMTP, el enlace para continuar la prueba.
  const [resultado, setResultado] = useState(null);

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
      const respuesta = await api.recuperarPassword(email);
      setResultado(respuesta);
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
          <span
            className={`mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full
                        border ${
                          resultado?.correo_operativo
                            ? "border-exito/30 bg-exito-suave text-exito"
                            : "border-aviso/30 bg-aviso-suave text-aviso"
                        }`}
          >
            {resultado?.correo_operativo ? (
              <MailCheck size={26} aria-hidden="true" />
            ) : (
              <MailWarning size={26} aria-hidden="true" />
            )}
          </span>

          {resultado?.correo_operativo ? (
            <>
              <h2 className="font-display text-2xl">Revisa tu correo</h2>
              <p className="mb-7 mt-3 text-sm leading-relaxed text-ink-soft">
                Si <strong className="text-ink">{email}</strong> corresponde a una cuenta
                registrada, recibirás en unos minutos un mensaje con el enlace para
                crear una contraseña nueva.
              </p>
            </>
          ) : (
            <>
              <h2 className="font-display text-2xl">Solicitud registrada</h2>
              {/* Decirlo es mejor que dejar a alguien esperando un correo que
                  nunca va a llegar porque el servidor no tiene SMTP. */}
              <p className="mt-3 text-sm leading-relaxed text-ink-soft">
                El envío de correo no está configurado en este servidor, así que
                <strong className="text-ink"> no se ha enviado ningún mensaje</strong>.
                Contacta con la galería para que te restablezcan la contraseña.
              </p>

              {resultado?.enlace_desarrollo && (
                <div className="mt-5 rounded-lg border border-line bg-paper-dim/60 p-4 text-left">
                  <p className="etiqueta mb-2 text-muted">Entorno de desarrollo</p>
                  <p className="mb-3 text-xs leading-relaxed text-ink-soft">
                    Como no hay servidor de correo, este es el enlace que se habría
                    enviado. Caduca en 30 minutos.
                  </p>
                  <a
                    href={resultado.enlace_desarrollo}
                    className="block break-all rounded border border-line bg-paper px-3 py-2
                               font-mono text-[11px] text-forest underline
                               underline-offset-2 hover:text-sienna"
                  >
                    {resultado.enlace_desarrollo}
                  </a>
                </div>
              )}

              <div className="mb-7" />
            </>
          )}

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
