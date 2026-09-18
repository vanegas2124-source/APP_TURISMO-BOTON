# ============================================================
# modelo_ml_recomendacion.py
# APP TURISMO - MODELO DE RECOMENDACIÓN
# ============================================================

from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List, Optional

import joblib
import pandas as pd


# ============================================================
# RUTA DEL MODELO
# ============================================================

ARCHIVO_ACTUAL = Path(__file__).resolve()

# Este archivo está en:
# ai_service/app/ml_turismo/
#
# parents[2] = ai_service/
AI_SERVICE_DIR = ARCHIVO_ACTUAL.parents[2]

RUTA_MODELO = (
    AI_SERVICE_DIR
    / "modelos"
    / "modelo_recomendacion.pkl"
)


# ============================================================
# COLUMNAS UTILIZADAS EN EL ENTRENAMIENTO
# ============================================================

COLUMNAS_ENTRADA = [
    "edad",
    "compania",
    "condicion_fisica",
    "discapacidad_fisica",
    "enfermedad",
    "actividades_preferidas",
    "gusto_naturaleza",
    "gusto_aventura",
    "importancia_seguridad",
    "distancia",
    "duracion",
    "presupuesto",
    "acepta_lluvia",
    "clima_preferido",
    "riesgo_aceptado",
    "riesgos_preocupantes"
]


# ============================================================
# CARGAR MODELO
# ============================================================

@lru_cache(maxsize=1)
def cargar_modelo_recomendacion():
    """
    Carga el modelo de recomendación desde ai_service/modelos.

    El modelo queda almacenado en memoria para evitar
    leer el .pkl en cada solicitud.
    """

    if not RUTA_MODELO.exists():
        raise FileNotFoundError(
            "\nNo se encontró el modelo de recomendación.\n"
            f"Ruta esperada:\n{RUTA_MODELO}\n\n"
            "Ejecuta primero:\n"
            "python app\\ml_turismo\\entrenar_modelos.py"
        )

    modelo = joblib.load(
        RUTA_MODELO
    )

    return modelo


# ============================================================
# PREPARAR DATOS DEL USUARIO
# ============================================================

def preparar_entrada(
    usuario: Dict[str, Any]
) -> pd.DataFrame:
    """
    Convierte los datos del usuario al mismo formato
    utilizado durante el entrenamiento.
    """

    datos = {}

    for columna in COLUMNAS_ENTRADA:

        valor = usuario.get(
            columna,
            "No responde"
        )

        # Evitar None
        if valor is None:
            valor = "No responde"

        # Convertir listas en texto
        if isinstance(valor, list):
            valor = ", ".join(
                str(item)
                for item in valor
            )

        # El entrenamiento convirtió todo a string
        datos[columna] = [
            str(valor)
        ]

    return pd.DataFrame(
        datos,
        columns=COLUMNAS_ENTRADA
    )


# ============================================================
# GENERAR RECOMENDACIÓN
# ============================================================

def recomendar_lugar(
    usuario: Dict[str, Any],
    top_n: Optional[int] = 3
) -> Dict[str, Any]:
    """
    Genera una recomendación turística basada en
    el perfil del usuario.

    Devuelve:
        - lugar recomendado
        - probabilidad del lugar recomendado
        - Top 3
        - ranking completo o limitado por top_n
    """

    # ----------------------------------------
    # Validar top_n
    # ----------------------------------------

    if top_n is not None and top_n < 1:
        raise ValueError(
            "top_n debe ser mayor o igual a 1 "
            "o puede ser None."
        )


    # ----------------------------------------
    # Cargar modelo
    # ----------------------------------------

    modelo = cargar_modelo_recomendacion()


    # ----------------------------------------
    # Preparar entrada
    # ----------------------------------------

    entrada = preparar_entrada(
        usuario
    )


    # ----------------------------------------
    # Predicción principal
    # ----------------------------------------

    lugar_predicho = modelo.predict(
        entrada
    )[0]


    ranking_completo: List[
        Dict[str, Any]
    ] = []


    # ----------------------------------------
    # Obtener probabilidades
    # ----------------------------------------

    if hasattr(
        modelo,
        "predict_proba"
    ):

        probabilidades = (
            modelo.predict_proba(
                entrada
            )[0]
        )

        clases = list(
            modelo.classes_
        )


        for lugar, probabilidad in zip(
            clases,
            probabilidades
        ):

            ranking_completo.append(
                {
                    "lugar": str(lugar),
                    "probabilidad": round(
                        float(probabilidad),
                        4
                    )
                }
            )


        # ----------------------------------------
        # Ordenar mayor → menor probabilidad
        # ----------------------------------------

        ranking_completo = sorted(
            ranking_completo,
            key=lambda item:
                item["probabilidad"],
            reverse=True
        )


        # ----------------------------------------
        # Agregar posición
        # ----------------------------------------

        for indice, item in enumerate(
            ranking_completo,
            start=1
        ):

            item["posicion"] = indice


    # ----------------------------------------
    # Si por alguna razón no hay predict_proba
    # ----------------------------------------

    if not ranking_completo:

        ranking_completo = [
            {
                "lugar": str(
                    lugar_predicho
                ),
                "probabilidad": None,
                "posicion": 1
            }
        ]


    # ----------------------------------------
    # Top 3
    # ----------------------------------------

    top_3 = (
        ranking_completo[:3]
    )


    # ----------------------------------------
    # Ranking solicitado
    # ----------------------------------------

    if top_n is None:

        ranking = (
            ranking_completo
        )

    else:

        ranking = (
            ranking_completo[:top_n]
        )


    # ----------------------------------------
    # Lugar principal
    # ----------------------------------------

    lugar_recomendado = (
        ranking_completo[0]["lugar"]
    )


    probabilidad_recomendacion = (
        ranking_completo[0][
            "probabilidad"
        ]
    )


    # ----------------------------------------
    # Resultado
    # ----------------------------------------

    return {

        "modelo":
            "recomendacion",

        "lugar_recomendado":
            lugar_recomendado,

        "probabilidad_recomendacion":
            probabilidad_recomendacion,

        "top_3":
            top_3,

        "ranking":
            ranking
    }