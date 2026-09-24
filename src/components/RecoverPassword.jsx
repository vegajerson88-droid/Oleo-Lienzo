import { useState } from "react";
import { Link } from "react-router-dom";
import Input from "./ui/Input";
import Button from "./ui/Button";
import { validateField } from "../utils/validators";

function RecoverPassword({ onBackToLogin }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [touched, setTouched] = useState(false);
  const [enviado, setEnviado] = useState(false);

  const handleChange = (e) => {
    const { value } = e.target;
    setEmail(value);
    setTouched(true);
    setError(validateField("email", value));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const message = validateField("email", email);
    setError(message);
    setTouched(true);
    if (!message) {
      setEnviado(true);
    }
  };

  return (
    <div className="bg-paper border-t-4 border-gold rounded-xl p-7 sm:p-10 shadow-xl shadow-ink/10 max-w-md w-full mx-auto">
      <h2 className="font-display text-2xl mb-2">Recuperar contraseña</h2>
      <p className="text-sm text-ink/70 mb-6">
        Escribe tu correo y te enviaremos las instrucciones para restablecer
        tu contraseña.
      </p>

      {enviado ? (
        <div>
          <p className="text-sm text-forest mb-6">
            Si <strong>{email}</strong> está registrado, recibirás un correo
            con los pasos para recuperar tu contraseña en unos minutos.
          </p>
          <Button variant="outline" className="w-full" onClick={onBackToLogin}>
            Volver a iniciar sesión
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
          <Input
            label="Correo electrónico"
            name="email"
            type="email"
            value={email}
            onChange={handleChange}
            error={touched && error}
            maxLength={80}
          />
          <Button type="submit">Recuperar contraseña</Button>
          {onBackToLogin ? (
            <button
              type="button"
              onClick={onBackToLogin}
              className="text-xs font-mono uppercase tracking-wider text-ink/60 hover:text-forest text-center"
            >
              Volver a iniciar sesión
            </button>
          ) : (
            <Link
              to="/login"
              className="text-xs font-mono uppercase tracking-wider text-ink/60 hover:text-forest text-center"
            >
              Volver a iniciar sesión
            </Link>
          )}
        </form>
      )}
    </div>
  );
}

export default RecoverPassword;
