"""IA local: sugiere un precio estimado para una obra según año y técnica.

El modelo se entrena una sola vez a partir de datos de ejemplo (ver seed.py /
artData.js) y se carga una única vez en el lifespan de la aplicación
(app.state.ai_local_model). Si el modelo no existe, la API igual arranca:
el endpoint simplemente informa que el modelo no está disponible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "modelo_precio.joblib"
MODEL_VERSION = "1.0-linear"
VARIABLES_UTILIZADAS = ["anio", "tecnica_oleo (0/1)"]


@dataclass
class ModeloPrecio:
    modelo: LinearRegression
    version: str = MODEL_VERSION


def entrenar_y_guardar(obras: list[dict]) -> None:
    """Entrena con una lista de dicts {anio, tecnica, precio} y persiste con joblib."""
    if len(obras) < 4:
        return  # datos insuficientes; no se genera el modelo
    X = np.array([[o["anio"], 1.0 if "óleo" in o["tecnica"].lower() else 0.0] for o in obras])
    y = np.array([o["precio"] for o in obras])
    modelo = LinearRegression()
    modelo.fit(X, y)
    joblib.dump(ModeloPrecio(modelo=modelo), MODEL_PATH)


def cargar_modelo() -> ModeloPrecio | None:
    if not MODEL_PATH.exists():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def predecir_precio(modelo: ModeloPrecio | None, anio: int, tecnica: str) -> dict:
    if modelo is None:
        return {
            "disponible": False,
            "detalle": "El modelo de IA local no está entrenado todavía "
            "(faltan datos suficientes de obras). Ejecuta seed.py con más registros.",
        }
    es_oleo = 1.0 if "óleo" in tecnica.lower() else 0.0
    x = np.array([[anio, es_oleo]])
    precio_estimado = float(modelo.modelo.predict(x)[0])
    return {
        "disponible": True,
        "precio_estimado": round(max(precio_estimado, 0), 2),
        "variables_utilizadas": VARIABLES_UTILIZADAS,
        "version_modelo": modelo.version,
    }
