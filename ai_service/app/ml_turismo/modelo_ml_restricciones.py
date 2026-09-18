# ============================================================
# modelo_ml_restricciones.py
# APP TURISMO - MODELO DE RESTRICCIONES
# ============================================================

from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List

import joblib
import pandas as pd


# ============================================================
# RUTA DEL MODELO
# ============================================================

ARCHIVO_ACTUAL = Path(__file__).resolve()

# modelo_ml_restricciones.py está en:
# ai_service/app/ml_turismo/
#
# parents[2] = ai_service/
AI_SERVICE_DIR = ARCHIVO_ACTUAL.parents[2]

RUTA_MODELO = (
    AI_SERVICE_DIR
    / "modelos"
    / "modelo_restricciones.pkl"
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
def cargar_modelo_restricciones():
    """
    Carga el modelo de restricciones.

    lru_cache evita cargar nuevamente el archivo .pkl
    en cada solicitud realizada a FastAPI.
    """

    if not RUTA_MODELO.exists():
        raise FileNotFoundError(
            "\nNo se encontró el modelo de restricciones.\n"
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
    Convierte los datos recibidos del usuario al mismo
    formato utilizado durante el entrenamiento.

    Las listas se convierten a texto separado por comas.
    Todos los valores se convierten a string porque el
    pipeline fue entrenado con variables categóricas.
    """

    datos = {}

    for columna in COLUMNAS_ENTRADA:

        valor = usuario.get(
            columna,
            "No responde"
        )

        # ----------------------------------------
        # Evitar valores None
        # ----------------------------------------

        if valor is None:
            valor = "No responde"

        # ----------------------------------------
        # Convertir listas en texto
        # ----------------------------------------

        if isinstance(valor, list):
            valor = ", ".join(
                str(item)
                for item in valor
            )

        # ----------------------------------------
        # Convertir al mismo tipo del entrenamiento
        # ----------------------------------------

        datos[columna] = [
            str(valor)
        ]

    return pd.DataFrame(
        datos,
        columns=COLUMNAS_ENTRADA
    )


# ============================================================
# NOMBRE DE LA CLASE
# ============================================================

def nombre_clase_restriccion(
    clase
) -> str:

    try:
        clase_entera = int(clase)

    except (TypeError, ValueError):
        clase_entera = 0


    if clase_entera == 1:
        return "APTO"

    return "NO APTO"


# ============================================================
# REALIZAR PREDICCIÓN
# ============================================================

def predecir_restriccion(
    usuario: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evalúa si el perfil del turista es APTO o NO APTO.

    Devuelve:
        - resultado principal
        - apto True/False
        - probabilidad de aptitud
        - probabilidades de cada clase
    """

    # ----------------------------------------
    # Cargar modelo
    # ----------------------------------------

    modelo = cargar_modelo_restricciones()


    # ----------------------------------------
    # Preparar entrada
    # ----------------------------------------

    entrada = preparar_entrada(
        usuario
    )


    # ----------------------------------------
    # Predicción principal
    # ----------------------------------------

    prediccion = modelo.predict(
        entrada
    )[0]


    probabilidad_apto = None

    probabilidad_no_apto = None

    ranking: List[
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


        for clase, probabilidad in zip(
            clases,
            probabilidades
        ):

            clase_entera = int(
                clase
            )

            probabilidad_float = round(
                float(probabilidad),
                4
            )

            resultado = (
                nombre_clase_restriccion(
                    clase_entera
                )
            )


            ranking.append(
                {
                    "resultado": resultado,
                    "clase": clase_entera,
                    "probabilidad":
                        probabilidad_float
                }
            )


            if clase_entera == 1:

                probabilidad_apto = (
                    probabilidad_float
                )


            elif clase_entera == 0:

                probabilidad_no_apto = (
                    probabilidad_float
                )


        # ----------------------------------------
        # Ordenar probabilidades
        # ----------------------------------------

        ranking = sorted(
            ranking,
            key=lambda item:
                item["probabilidad"],
            reverse=True
        )


        for indice, item in enumerate(
            ranking,
            start=1
        ):

            item["posicion"] = indice


    # ----------------------------------------
    # Resultado
    # ----------------------------------------

    resultado_principal = (
        nombre_clase_restriccion(
            prediccion
        )
    )


    return {

        "modelo":
            "restricciones",

        "resultado_principal":
            resultado_principal,

        "apto":
            bool(
                int(prediccion) == 1
            ),

        "probabilidad_apto":
            probabilidad_apto,

        "probabilidad_no_apto":
            probabilidad_no_apto,

        "top_resultados":
            ranking
    }