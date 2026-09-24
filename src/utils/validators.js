/**
 * Validaciones de formulario del frontend.
 *
 * Son una comodidad para el usuario: avisan al instante de lo que está mal,
 * sin esperar al servidor. Las mismas reglas están repetidas en los esquemas
 * Pydantic del backend, que es quien valida de verdad. Si alguien salta este
 * código, el servidor responde 422 igualmente.
 */

export const PATRONES = {
  email: /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/,
  soloLetras: /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]{2,40}$/,
  soloNumeros: /^\d+$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$/,
};

const LIMITES = {
  numeroDocumento: { min: 6, max: 15, etiqueta: "dígitos" },
  telefono: { min: 7, max: 10, etiqueta: "dígitos" },
  direccion: { min: 5, max: 100, etiqueta: "caracteres" },
  asunto: { min: 5, max: 140, etiqueta: "caracteres" },
  mensaje: { min: 10, max: 2000, etiqueta: "caracteres" },
  respuesta: { min: 10, max: 2000, etiqueta: "caracteres" },
};

function validarLongitud(campo, valor) {
  const limite = LIMITES[campo];
  if (!limite) return "";
  if (valor.length < limite.min || valor.length > limite.max) {
    return `Debe tener entre ${limite.min} y ${limite.max} ${limite.etiqueta}.`;
  }
  return "";
}

/** Valida un campo concreto. Devuelve "" si es correcto. */
export function validateField(name, value, values = {}) {
  const v = (value ?? "").toString().trim();

  switch (name) {
    case "nombre":
    case "apellido":
      if (!v) return "Este campo es obligatorio.";
      if (!PATRONES.soloLetras.test(v))
        return "Solo se permiten letras y espacios (2 a 40 caracteres).";
      return "";

    case "tipoDocumento":
      return v ? "" : "Selecciona un tipo de documento.";

    case "numeroDocumento":
      if (!v) return "Este campo es obligatorio.";
      if (!PATRONES.soloNumeros.test(v)) return "Solo se permiten números.";
      return validarLongitud("numeroDocumento", v);

    case "telefono":
      if (!v) return "Este campo es obligatorio.";
      if (!PATRONES.soloNumeros.test(v)) return "Solo se permiten números.";
      return validarLongitud("telefono", v);

    case "direccion":
      if (!v) return "Este campo es obligatorio.";
      return validarLongitud("direccion", v);

    case "email":
    case "correo":
      if (!v) return "Este campo es obligatorio.";
      if (!PATRONES.email.test(v)) return "El formato del correo no es válido.";
      if (v.length > 80) return "El correo no puede superar los 80 caracteres.";
      return "";

    case "password":
      if (!v) return "Este campo es obligatorio.";
      if (!PATRONES.password.test(v))
        return "Mínimo 8 caracteres, con mayúscula, minúscula y número.";
      return "";

    case "confirmarPassword":
      if (!v) return "Confirma tu contraseña.";
      if (v !== values.password) return "Las contraseñas no coinciden.";
      return "";

    case "asunto":
      if (!v) return "Escribe un asunto.";
      return validarLongitud("asunto", v);

    case "mensaje":
      if (!v) return "Escribe tu mensaje.";
      return validarLongitud("mensaje", v);

    case "respuesta":
      if (!v) return "Escribe la respuesta.";
      return validarLongitud("respuesta", v);

    case "tipo":
      return v ? "" : "Selecciona el tipo de solicitud.";

    // ── Campos del catálogo (paneles de gestión) ──────────────────────
    case "titulo":
      if (!v) return "Este campo es obligatorio.";
      if (v.length < 2 || v.length > 120) return "Debe tener entre 2 y 120 caracteres.";
      return "";

    case "artista":
    case "tecnica":
      if (!v) return "Este campo es obligatorio.";
      if (v.length < 2 || v.length > 80) return "Debe tener entre 2 y 80 caracteres.";
      return "";

    case "anio": {
      if (!v) return "Este campo es obligatorio.";
      const anio = Number(v);
      const anioActual = new Date().getFullYear();
      if (!Number.isInteger(anio)) return "Escribe un año válido.";
      if (anio < 1400 || anio > anioActual) return `Debe estar entre 1400 y ${anioActual}.`;
      return "";
    }

    case "precio": {
      if (!v) return "Este campo es obligatorio.";
      const precio = Number(v);
      if (Number.isNaN(precio)) return "Escribe un número válido.";
      if (precio <= 0) return "El precio debe ser mayor que cero.";
      if (precio > 999999999) return "El precio es demasiado alto.";
      return "";
    }

    case "stock": {
      if (v === "") return "Este campo es obligatorio.";
      const stock = Number(v);
      if (!Number.isInteger(stock)) return "Escribe un número entero.";
      if (stock < 0) return "El stock no puede ser negativo.";
      return "";
    }

    case "descripcion":
      if (!v) return "Este campo es obligatorio.";
      if (v.length < 5) return "Debe tener al menos 5 caracteres.";
      if (v.length > 2000) return "No puede superar los 2000 caracteres.";
      return "";

    case "nombreServicio":
      if (!v) return "Este campo es obligatorio.";
      if (v.length < 2 || v.length > 100) return "Debe tener entre 2 y 100 caracteres.";
      return "";

    default:
      return "";
  }
}

/** Valida una lista de campos y devuelve solo los que tienen error. */
export function validateForm(values, fields) {
  const errores = {};
  fields.forEach((campo) => {
    const mensaje = validateField(campo, values[campo], values);
    if (mensaje) errores[campo] = mensaje;
  });
  return errores;
}
