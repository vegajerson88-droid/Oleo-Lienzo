import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ArrowRight, LogIn } from "lucide-react";

import RecoverPassword from "../components/RecoverPassword";
import RegisterModal from "../components/RegisterModal";
import Logo from "../components/Logo";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { validateField } from "../utils/validators";

const VALORES_INICIALES = { email: "", password: "" };

/** Panel lateral decorativo con el argumento de venta de la galería. */
function PanelMarca() {
  return (
    <aside className="relative hidden overflow-hidden bg-gradient-to-br from-forest
                      to-forest-dark p-12 lg:flex lg:flex-col lg:justify-between">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.08]"
        aria-hidden="true"
        style={{
          backgroundImage:
            "radial-gradient(circle at 25% 25%, #c9a227 0%, transparent 45%), " +
            "radial-gradient(circle at 75% 75%, #c9a227 0%, transparent 45%)",
        }}
      />
      <div className="relative">
        <Logo tamano="lg" />
      </div>
      <div className="relative">
        <p className="font-display text-3xl leading-snug text-paper">
          «El arte no reproduce lo visible; lo hace visible.»
        </p>
        <p className="mt-4 etiqueta text-gold">Paul Klee</p>
      </div>
      <p className="relative text-sm leading-relaxed text-paper/60">
        Galería de arte contemporáneo especializada en piezas originales de
        pintores colombianos. Desde 2015.
      </p>
    </aside>
  );
}

function Login() {
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const { login, rutaPanel } = useAuth();
  const toast = useToast();

  const [valores, setValores] = useState(VALORES_INICIALES);
  const [errores, setErrores] = useState({});
  const [tocados, setTocados] = useState({});
  const [recordarme, setRecordarme] = useState(false);
  const [vista, setVista] = useState("login"); // "login" | "recuperar"
  const [modalAbierto, setModalAbierto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  function alCambiar(evento) {
    const { name, value } = evento.target;
    const siguiente = { ...valores, [name]: value };
    setValores(siguiente);
    setTocados((previos) => ({ ...previos, [name]: true }));
    setErrores((previos) => ({ ...previos, [name]: validateField(name, value, siguiente) }));
    if (errorServidor) setErrorServidor("");
  }

  async function alEnviar(evento) {
    evento.preventDefault();

    const errorEmail = validateField("email", valores.email);
    const errorPassword = valores.password ? "" : "Este campo es obligatorio.";
    setErrores({ email: errorEmail, password: errorPassword });
    setTocados({ email: true, password: true });
    if (errorEmail || errorPassword) return;

    setEnviando(true);
    setErrorServidor("");
    try {
      const usuario = await login(valores.email, valores.password, recordarme);
      toast.exito(`¡Bienvenido de nuevo, ${usuario.nombre}!`);

      // Vuelve a donde el usuario quería ir, o a su panel.
      const destino =
        ubicacion.state?.desde ||
        (usuario.rol.nombre === "administrador"
          ? "/panel/administrador"
          : usuario.rol.nombre === "empleado"
          ? "/panel/empleado"
          : "/panel/cliente");
      navegar(destino, { replace: true });
    } catch (error) {
      setErrorServidor(
        error.status === 429
          ? "Demasiados intentos seguidos. Espera un minuto antes de volver a probar."
          : error.message
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[1fr_1.1fr]">
      <PanelMarca />

      <div className="flex flex-col bg-wall">
        {/* Cabecera de marca, solo en pantallas donde no hay panel lateral */}
        <div className="border-b-[3px] border-gold bg-forest py-6 lg:hidden">
          <div className="contenedor flex justify-center">
            <Link to="/" aria-label="Óleo & Lienzo, ir al inicio">
              <Logo tamano="md" />
            </Link>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center px-4 py-10 sm:px-6">
          {vista === "recuperar" ? (
            <RecoverPassword onVolver={() => setVista("login")} />
          ) : (
            <div className="w-full max-w-md">
              <div className="rounded-2xl border-t-4 border-gold bg-paper p-7 shadow-media sm:p-9">
                <h1 className="font-display text-3xl">Iniciar sesión</h1>
                <p className="mb-7 mt-2 text-sm text-ink-soft">
                  Accede para gestionar tus pedidos, tus facturas y tus solicitudes.
                </p>

                <form onSubmit={alEnviar} noValidate className="flex flex-col gap-4">
                  <Input
                    label="Correo electrónico"
                    name="email"
                    type="email"
                    autoComplete="email"
                    value={valores.email}
                    onChange={alCambiar}
                    error={tocados.email ? errores.email : ""}
                    valido={tocados.email && !errores.email && Boolean(valores.email)}
                    maxLength={80}
                    required
                  />
                  <Input
                    label="Contraseña"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    value={valores.password}
                    onChange={alCambiar}
                    error={tocados.password ? errores.password : ""}
                    maxLength={64}
                    required
                  />

                  {errorServidor && <Alert tipo="error">{errorServidor}</Alert>}

                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <label className="flex cursor-pointer items-center gap-2 text-sm text-ink-soft">
                      <input
                        type="checkbox"
                        checked={recordarme}
                        onChange={(evento) => setRecordarme(evento.target.checked)}
                        className="h-4 w-4 accent-forest"
                      />
                      No cerrar sesión
                    </label>
                    <button
                      type="button"
                      onClick={() => setVista("recuperar")}
                      className="etiqueta text-muted transition-colors hover:text-forest"
                    >
                      ¿Olvidaste tu contraseña?
                    </button>
                  </div>

                  <Button
                    type="submit"
                    size="lg"
                    cargando={enviando}
                    iconoIzquierda={LogIn}
                    className="mt-1 w-full"
                  >
                    {enviando ? "Entrando…" : "Iniciar sesión"}
                  </Button>
                </form>

                <div className="mt-7 border-t border-line pt-5 text-center">
                  <p className="text-sm text-ink-soft">
                    ¿No tienes cuenta?{" "}
                    <button
                      type="button"
                      onClick={() => setModalAbierto(true)}
                      className="font-semibold text-forest underline underline-offset-2
                                 transition-colors hover:text-gold"
                    >
                      Crear una cuenta
                    </button>
                  </p>
                </div>
              </div>

              <Link
                to="/"
                className="mt-5 flex items-center justify-center gap-1.5 etiqueta text-muted
                           transition-colors hover:text-forest"
              >
                Volver a la galería
                <ArrowRight size={12} aria-hidden="true" />
              </Link>
            </div>
          )}
        </div>
      </div>

      <RegisterModal
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        onSuccess={(datos) => {
          setValores((previos) => ({ ...previos, email: datos.email }));
        }}
      />
    </div>
  );
}

export default Login;
