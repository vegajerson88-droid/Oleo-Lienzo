export const PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/,
  soloLetras: /^[A-Za-zÁÉÍÓÚÁáéíóúñÑ\s]{2,40}$/,
  soloNumeros: /^\d+$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$/,
};

export function validateField(name, value, values = {}) {
  const v = (value ?? "").toString().trim();

  switch (name) {
    case "nombre":
    case "apellido":
      if (!v) return "Este campo es obligatorio.";
      if (!PATTERNS.soloLetras.test(v))
        return "Solo se permiten letras y espacios (2 a 40 caracteres).";
      return "";

    case "tipoDocumento":
      if (!v) return "Selecciona un tipo de documento.";
      return "";

    case "numeroDocumento":
      if (!v) return "Este campo es obligatorio.";
      if (!PATTERNS.soloNumeros.test(v)) return "Solo se permiten números.";
      if (v.length < 6 || v.length > 15)
        return "Debe tener entre 6 y 15 dígitos.";
      return "";

    case "direccion":
      if (!v) return "Este campo es obligatorio.";
      if (v.length < 5 || v.length > 100)
        return "Debe tener entre 5 y 100 caracteres.";
      return "";

    case "telefono":
      if (!v) return "Este campo es obligatorio.";
      if (!PATTERNS.soloNumeros.test(v)) return "Solo se permiten números.";
      if (v.length < 7 || v.length > 10)
        return "Debe tener entre 7 y 10 dígitos.";
      return "";

    case "email":
      if (!v) return "Este campo es obligatorio.";
      if (!PATTERNS.email.test(v)) return "El formato del correo no es válido.";
      return "";

    case "password":
      if (!v) return "Este campo es obligatorio.";
      if (!PATTERNS.password.test(v))
        return "Mínimo 8 caracteres, con mayúscula, minúscula y número.";
      return "";

    case "confirmarPassword":
      if (!v) return "Confirma tu contraseña.";
      if (v !== values.password) return "Las contraseñas no coinciden.";
      return "";

    default:
      return "";
  }
}

export function validateForm(values, fields) {
  const errors = {};
  fields.forEach((field) => {
    const message = validateField(field, values[field], values);
    if (message) errors[field] = message;
  });
  return errors;
}
