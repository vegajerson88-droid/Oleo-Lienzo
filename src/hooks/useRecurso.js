import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Carga un recurso de la API gestionando carga, error y recarga.
 *
 * Centraliza el patrón que si no se repetiría en cada pantalla, y cancela la
 * petición en curso cuando el componente se desmonta o cambian los filtros,
 * para no escribir estado sobre un componente que ya no existe.
 *
 *   const { datos, cargando, error, recargar } = useRecurso(
 *     (signal) => api.listarObras({ page }, signal),
 *     [page]
 *   );
 */
export function useRecurso(cargador, dependencias = [], { inmediato = true } = {}) {
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(inmediato);
  const [error, setError] = useState(null);

  const cargadorRef = useRef(cargador);
  cargadorRef.current = cargador;

  const controladorRef = useRef(null);
  const montadoRef = useRef(true);

  useEffect(() => {
    montadoRef.current = true;
    return () => {
      montadoRef.current = false;
      controladorRef.current?.abort();
    };
  }, []);

  const ejecutar = useCallback(async () => {
    controladorRef.current?.abort();
    const controlador = new AbortController();
    controladorRef.current = controlador;

    setCargando(true);
    setError(null);
    try {
      const resultado = await cargadorRef.current(controlador.signal);
      if (montadoRef.current && !controlador.signal.aborted) setDatos(resultado);
      return resultado;
    } catch (fallo) {
      if (fallo.name === "AbortError") return undefined;
      if (montadoRef.current) setError(fallo);
      return undefined;
    } finally {
      if (montadoRef.current && !controlador.signal.aborted) setCargando(false);
    }
  }, []);

  useEffect(() => {
    if (inmediato) ejecutar();
    // Las dependencias las decide quien usa el hook.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencias);

  return { datos, cargando, error, recargar: ejecutar, setDatos };
}

/**
 * Envuelve una acción (crear, actualizar, borrar) con su estado de envío.
 *
 *   const { ejecutar, enviando, error } = useAccion(async (datos) => { ... });
 */
export function useAccion(accion) {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);

  const accionRef = useRef(accion);
  accionRef.current = accion;

  const ejecutar = useCallback(async (...args) => {
    setEnviando(true);
    setError(null);
    try {
      return await accionRef.current(...args);
    } catch (fallo) {
      setError(fallo);
      throw fallo;
    } finally {
      setEnviando(false);
    }
  }, []);

  return { ejecutar, enviando, error, limpiarError: () => setError(null) };
}
