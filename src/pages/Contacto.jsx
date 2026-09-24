import { useState } from "react";
import { Clock, Mail, MapPin, Phone, Send } from "lucide-react";

import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Textarea from "../components/ui/Textarea";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { api } from "../services/api";
import { validateField, validateForm } from "../utils/validators";

const TIPOS = [
  { value: "peticion", label: "Petición" },
  { value: "queja", label: "Queja" },
  { value: "reclamo", label: "Reclamo" },
  { value: "sugerencia", label: "Sugerencia" },
];

const DATOS_GALERIA = [
  { Icono: MapPin, titulo: "Dirección", texto: "Calle 45 # 12-30, Bogotá D.C." },
  { Icono: Clock, titulo: "Horario", texto: "Martes a sábado, 10:00 a.m. – 6:00 p.m." },
  { Icono: Phone, titulo: "Teléfono", texto: "+57 300 123 4567" },
  { Icono: Mail, titulo: "Correo", texto: "contacto@oleoylienzo.com" },
];

/**
 * Contacto y radicación de PQR.
 *
 * El formulario escribe de verdad en la base de datos a través del módulo de
 * PQR: devuelve un número de radicado con el que hacer seguimiento. Funciona
 * con y sin sesión iniciada; sin ella pide los datos de contacto.
 */
function Contacto() {
  const { autenticado, usuario, token } = useAuth();
  const toast = useToast();

  const camposBase = ["tipo", "asunto", "mensaje"];
  const campos = autenticado ? camposBase : [...camposBase, "nombre", "correo"];

  const [valores, setValores] = useState({
    tipo: "peticion", asunto: "", mensaje: "", nombre: "", correo: "",
  });
  const [errores, setErrores] = useState({});
  const [tocados, setTocados] = useState({});
  const [enviando, setEnviando] = useState(false);
  const [radicado, setRadicado] = useState(null);
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

    const encontrados = validateForm(valores, campos);
    setErrores(encontrados);
    setTocados(Object.fromEntries(campos.map((campo) => [campo, true])));
    if (Object.keys(encontrados).length > 0) return;

    setEnviando(true);
    setErrorServidor("");
    try {
      const datos = {
        tipo: valores.tipo,
        asunto: valores.asunto,
        mensaje: valores.mensaje,
        ...(autenticado
          ? {}
          : { contacto_nombre: valores.nombre, contacto_email: valores.correo }),
      };
      const creada = await api.radicarPqr(datos, token);
      setRadicado(creada.radicado);
      toast.exito(`Solicitud radicada con el número ${creada.radicado}.`);
      setValores({ tipo: "peticion", asunto: "", mensaje: "", nombre: "", correo: "" });
      setTocados({});
    } catch (error) {
      setErrorServidor(error.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="contenedor max-w-5xl py-12 sm:py-16">
      <header className="mb-10">
        <span className="etiqueta text-sienna">Hablemos</span>
        <h1 className="mb-4 mt-2 font-display text-3xl sm:text-4xl">Contacto y PQR</h1>
        <p className="max-w-2xl text-sm text-ink-soft sm:text-base">
          ¿Te interesa una pieza, quieres agendar una visita o necesitas presentar
          una petición, queja o reclamo? Escríbenos y te damos un número de
          radicado para hacer seguimiento.
        </p>
      </header>

      <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[1.4fr_1fr]">
        <div className="tarjeta border-t-4 border-t-gold p-6 sm:p-8">
          {radicado && (
            <Alert tipo="exito" titulo={`Solicitud radicada: ${radicado}`} className="mb-6">
              Guarda este número para hacer seguimiento. Te enviamos una copia al
              correo y responderemos por esa misma vía.
            </Alert>
          )}

          <form onSubmit={alEnviar} noValidate className="flex flex-col gap-4">
            <Select
              label="Tipo de solicitud"
              name="tipo"
              value={valores.tipo}
              onChange={alCambiar}
              error={tocados.tipo ? errores.tipo : ""}
              options={TIPOS}
              required
            />

            {!autenticado && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Input
                  label="Nombre" name="nombre" autoComplete="name"
                  value={valores.nombre} onChange={alCambiar}
                  error={tocados.nombre ? errores.nombre : ""}
                  maxLength={40} required
                />
                <Input
                  label="Correo electrónico" name="correo" type="email" autoComplete="email"
                  value={valores.correo} onChange={alCambiar}
                  error={tocados.correo ? errores.correo : ""}
                  maxLength={80} required
                />
              </div>
            )}

            {autenticado && (
              <Alert tipo="info">
                La solicitud quedará a tu nombre: {usuario?.nombre} {usuario?.apellido} ·{" "}
                {usuario?.email}
              </Alert>
            )}

            <Input
              label="Asunto" name="asunto"
              value={valores.asunto} onChange={alCambiar}
              error={tocados.asunto ? errores.asunto : ""}
              placeholder="Resume tu solicitud en una línea"
              maxLength={140} contador required
            />

            <Textarea
              label="Mensaje" name="mensaje" rows={6}
              value={valores.mensaje} onChange={alCambiar}
              error={tocados.mensaje ? errores.mensaje : ""}
              placeholder="Cuéntanos con detalle qué necesitas…"
              maxLength={2000} contador required
            />

            {errorServidor && <Alert tipo="error">{errorServidor}</Alert>}

            <Button
              type="submit" size="lg" cargando={enviando}
              iconoIzquierda={Send} className="self-start"
            >
              {enviando ? "Enviando…" : "Enviar solicitud"}
            </Button>
          </form>
        </div>

        <aside className="tarjeta border-t-4 border-t-gold p-6 sm:p-8">
          <h2 className="mb-5 font-display text-lg">Visítanos</h2>
          <ul className="space-y-5">
            {DATOS_GALERIA.map(({ Icono, titulo, texto }) => (
              <li key={titulo} className="flex items-start gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg
                                 bg-paper-dim text-forest">
                  <Icono size={16} aria-hidden="true" />
                </span>
                <div>
                  <p className="etiqueta text-muted">{titulo}</p>
                  <p className="mt-0.5 text-sm text-ink-soft">{texto}</p>
                </div>
              </li>
            ))}
          </ul>

          <p className="mt-6 border-t border-line pt-5 text-xs leading-relaxed text-muted">
            También puedes escribirnos por WhatsApp o preguntarle al asistente
            virtual, con los botones de la esquina inferior derecha.
          </p>
        </aside>
      </div>
    </div>
  );
}

export default Contacto;
