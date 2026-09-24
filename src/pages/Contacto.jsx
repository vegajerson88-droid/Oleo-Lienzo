import { useState } from "react";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";

const initialValues = { nombre: "", correo: "", mensaje: "" };

function validate(values) {
  const errors = {};
  if (!values.nombre.trim()) errors.nombre = "Este campo es obligatorio.";
  else if (values.nombre.trim().length < 2)
    errors.nombre = "Debe tener al menos 2 caracteres.";

  if (!values.correo.trim()) errors.correo = "Este campo es obligatorio.";
  else if (!/^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/.test(values.correo))
    errors.correo = "El formato del correo no es válido.";

  if (!values.mensaje.trim()) errors.mensaje = "Escribe tu mensaje.";
  else if (values.mensaje.trim().length < 10)
    errors.mensaje = "Cuéntanos un poco más (mínimo 10 caracteres).";

  return errors;
}

function Contacto() {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [enviado, setEnviado] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const next = { ...values, [name]: value };
    setValues(next);
    setErrors((prev) => ({ ...prev, ...validate(next) }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const foundErrors = validate(values);
    setErrors(foundErrors);
    if (Object.keys(foundErrors).length === 0) {
      setEnviado(true);
    }
  };

  return (
    <div className="container mx-auto max-w-4xl px-6 py-14 sm:py-20">
      <span className="font-mono text-xs uppercase tracking-widest text-sienna">
        Hablemos
      </span>
      <h1 className="font-display text-3xl sm:text-4xl mt-2 mb-5">Contacto</h1>
      <p className="text-ink/80 max-w-xl mb-10 text-sm sm:text-base">
        ¿Te interesa una pieza en particular o quieres agendar una visita a
        la galería? Escríbenos y te respondemos en menos de 24 horas.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-[1.4fr_1fr] gap-8 items-start">
        <form
          onSubmit={handleSubmit}
          noValidate
          className="bg-paper border-t-4 border-gold rounded-xl p-6 sm:p-8 flex flex-col gap-5 shadow-sm"
        >
          <Input
            label="Nombre"
            name="nombre"
            value={values.nombre}
            onChange={handleChange}
            error={errors.nombre}
            maxLength={60}
          />
          <Input
            label="Correo electrónico"
            name="correo"
            type="email"
            value={values.correo}
            onChange={handleChange}
            error={errors.correo}
            maxLength={80}
          />
          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-xs uppercase tracking-wider text-ink/80">
              Mensaje
            </span>
            <textarea
              name="mensaje"
              rows="5"
              value={values.mensaje}
              onChange={handleChange}
              maxLength={500}
              className={`rounded-md border px-3 py-2.5 text-sm text-ink bg-white resize-y
                focus:outline-none focus:ring-2 focus:ring-gold/60
                ${errors.mensaje ? "border-sienna" : "border-ink/20"}`}
            />
            {errors.mensaje && (
              <span className="text-xs text-sienna">{errors.mensaje}</span>
            )}
          </label>

          <Button type="submit" className="self-start">
            Enviar mensaje
          </Button>

          {enviado && (
            <p className="text-sm text-forest">
              ¡Gracias! Recibimos tu mensaje y te contactaremos pronto.
            </p>
          )}
        </form>

        <div className="bg-paper border-t-4 border-gold rounded-xl p-6 sm:p-8 shadow-sm">
          <h3 className="font-display text-lg mb-3">Visítanos</h3>
          <p className="text-sm text-ink/75 mb-1.5">
            Calle 45 # 12-30, Bogotá D.C.
          </p>
          <p className="text-sm text-ink/75 mb-1.5">
            Martes a sábado, 10:00 a.m. – 6:00 p.m.
          </p>
          <p className="text-sm text-ink/75 mb-1.5">
            contacto@oleoylienzo.com
          </p>
          <p className="text-sm text-ink/75">+57 300 123 4567</p>
        </div>
      </div>
    </div>
  );
}

export default Contacto;
