import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import RecoverPassword from "../components/RecoverPassword";
import RegisterModal from "../components/RegisterModal";
import WhatsAppButton from "../components/WhatsAppButton";
import { validateField } from "../utils/validators";
import { useAuth } from "../context/AuthContext";

const initialValues = { email: "", password: "" };

function BrandBar() {
  return (
    <div className="bg-forest border-b-[3px] border-gold py-7 sm:py-8">
      <div className="container mx-auto max-w-6xl px-6 flex justify-center">
        <Link to="/" className="flex items-center gap-4">
          <span className="flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 rounded-full border-2 border-gold font-display italic text-gold text-2xl">
            O
          </span>
          <span className="font-display text-2xl sm:text-3xl text-paper">
            Óleo<span className="text-gold italic px-1">&amp;</span>Lienzo
          </span>
        </Link>
      </div>
    </div>
  );
}

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [recordarme, setRecordarme] = useState(false);
  const [vista, setVista] = useState("login"); // "login" | "recuperar"
  const [modalAbierto, setModalAbierto] = useState(false);
  const [sesionIniciada, setSesionIniciada] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    const next = { ...values, [name]: value };
    setValues(next);
    setTouched((prev) => ({ ...prev, [name]: true }));
    setErrors((prev) => ({ ...prev, [name]: validateField(name, value, next) }));
    if (errorServidor) setErrorServidor("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const emailError = validateField("email", values.email);
    const passwordError = values.password ? "" : "Este campo es obligatorio.";
    setErrors({ email: emailError, password: passwordError });
    setTouched({ email: true, password: true });
    if (emailError || passwordError) return;

    setEnviando(true);
    setErrorServidor("");
    try {
      await login(values.email, values.password);
      setSesionIniciada(true);
    } catch (err) {
      setErrorServidor(err.message || "No se pudo iniciar sesión.");
    } finally {
      setEnviando(false);
    }
  };

  if (vista === "recuperar") {
    return (
      <div className="min-h-screen flex flex-col bg-wall">
        <BrandBar />
        <div className="flex-1 flex items-center container mx-auto px-6 py-10">
          <RecoverPassword onBackToLogin={() => setVista("login")} />
        </div>
        <WhatsAppButton />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-wall">
      <BrandBar />
      <div className="flex-1 flex items-center container mx-auto px-6 py-12">
      <div className="bg-paper border-t-4 border-gold rounded-xl p-7 sm:p-10 shadow-xl shadow-ink/10 max-w-md w-full mx-auto">
        <h1 className="font-display text-3xl mb-2">Iniciar sesión</h1>
        <p className="text-sm text-ink/70 mb-7">
          Ingresa con tu correo y contraseña para ver tus obras favoritas y
          tus pedidos.
        </p>

        {sesionIniciada ? (
          <div>
            <p className="text-sm text-forest mb-6">
              ¡Bienvenido de nuevo! Iniciaste sesión correctamente.
            </p>
            <Button className="w-full" onClick={() => navigate("/")}>
              Ir a la galería
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
            <Input
              label="Correo electrónico"
              name="email"
              type="email"
              value={values.email}
              onChange={handleChange}
              error={touched.email && errors.email}
              maxLength={80}
            />
            <Input
              label="Contraseña"
              name="password"
              type="password"
              value={values.password}
              onChange={handleChange}
              error={touched.password && errors.password}
              maxLength={64}
            />

            {errorServidor && (
              <p className="text-sm text-sienna bg-sienna/10 border border-sienna/30 rounded-md px-3 py-2">
                {errorServidor}
              </p>
            )}

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-ink/75">
                <input
                  type="checkbox"
                  checked={recordarme}
                  onChange={(e) => setRecordarme(e.target.checked)}
                  className="w-4 h-4 accent-forest"
                />
                Recordarme
              </label>
              <button
                type="button"
                onClick={() => setVista("recuperar")}
                className="text-xs font-mono uppercase tracking-wider text-ink/60 hover:text-forest"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>

            <Button type="submit" disabled={enviando}>
              {enviando ? "Ingresando..." : "Iniciar sesión"}
            </Button>

            <p className="text-center text-sm text-ink/70">
              ¿No tienes cuenta?{" "}
              <button
                type="button"
                onClick={() => setModalAbierto(true)}
                className="text-forest font-medium hover:underline"
              >
                Crear una cuenta
              </button>
            </p>
          </form>
        )}
      </div>
      </div>

      <RegisterModal
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
      />
      <WhatsAppButton />
    </div>
  );
}

export default Login;
