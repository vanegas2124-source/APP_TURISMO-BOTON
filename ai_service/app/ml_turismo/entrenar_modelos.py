# ============================================================
# entrenar_modelos.py
# APP TURISMO - MÓDULO MACHINE LEARNING
#
# Entrena:
#   1. Modelo de restricciones
#   2. Modelo de recomendación
#
# Los datos se obtienen directamente desde Supabase.
# ============================================================

import os
from pathlib import Path

import joblib
import pandas as pd

from dotenv import load_dotenv
from supabase import create_client, Client

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

ARCHIVO_ACTUAL = Path(__file__).resolve()

# Si este archivo está en:
# ai_service/app/ml_turismo/entrenar_modelos.py
#
# parents[2] corresponde a:
# ai_service/
AI_SERVICE_DIR = ARCHIVO_ACTUAL.parents[2]

# Los modelos se guardarán en:
# ai_service/modelos/
RUTA_MODELOS = AI_SERVICE_DIR / "modelos"


# ============================================================
# BUSCAR .ENV
# ============================================================

def buscar_archivo_env():
    """
    Busca automáticamente el archivo .env subiendo
    desde la ubicación de este archivo hasta la raíz
    del proyecto.
    """

    carpeta_actual = ARCHIVO_ACTUAL.parent

    while True:
        candidato = carpeta_actual / ".env"

        if candidato.exists():
            return candidato

        if carpeta_actual.parent == carpeta_actual:
            break

        carpeta_actual = carpeta_actual.parent

    return None


ENV_PATH = buscar_archivo_env()

if ENV_PATH:
    load_dotenv(ENV_PATH)

    print(
        f"Archivo .env encontrado en: {ENV_PATH}"
    )
else:
    # También permite utilizar variables de entorno
    # definidas directamente en el sistema.
    load_dotenv()

    print(
        "ADVERTENCIA: No se encontró archivo .env."
    )


# ============================================================
# CONFIGURACIÓN SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_KEY = (
    os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("SUPABASE_PUBLISHABLE_KEY")
)


if not SUPABASE_URL:
    raise RuntimeError(
        "No se encontró SUPABASE_URL en el archivo .env."
    )


if not SUPABASE_KEY:
    raise RuntimeError(
        "No se encontró SUPABASE_ANON_KEY "
        "ni SUPABASE_PUBLISHABLE_KEY en el archivo .env."
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# COLUMNAS UTILIZADAS POR LOS MODELOS
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
# CARGAR DATASET DESDE SUPABASE
# ============================================================

def cargar_dataset_desde_supabase() -> pd.DataFrame:
    """
    Obtiene todos los registros de
    public.dataset_entrenamiento desde Supabase.

    Se utiliza paginación para evitar problemas
    si posteriormente el dataset supera 1000 registros.
    """

    print("\nConectando con Supabase...")

    registros = []

    tamanio_pagina = 1000
    inicio = 0

    while True:

        fin = inicio + tamanio_pagina - 1

        respuesta = (
            supabase
            .table("dataset_entrenamiento")
            .select("*")
            .order("id")
            .range(inicio, fin)
            .execute()
        )

        datos = respuesta.data or []

        registros.extend(datos)

        if len(datos) < tamanio_pagina:
            break

        inicio += tamanio_pagina


    if not registros:
        raise ValueError(
            "La tabla dataset_entrenamiento "
            "está vacía o Supabase no permitió leerla."
        )


    df = pd.DataFrame(registros)

    print("Conexión con Supabase correcta.")

    print(
        f"Registros obtenidos: {len(df)}"
    )

    return df


# ============================================================
# LIMPIEZA DE DATOS
# ============================================================

def limpiar_datos(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()


    # ----------------------------------------
    # Verificar columnas de entrada
    # ----------------------------------------

    for columna in COLUMNAS_ENTRADA:

        if columna not in df.columns:
            df[columna] = "No responde"

        df[columna] = (
            df[columna]
            .fillna("No responde")
            .astype(str)
        )


    # ----------------------------------------
    # Verificar variable objetivo restricciones
    # ----------------------------------------

    if "apto" not in df.columns:

        raise ValueError(
            "La tabla dataset_entrenamiento "
            "debe tener la columna 'apto'."
        )


    # ----------------------------------------
    # Verificar variable objetivo recomendación
    # ----------------------------------------

    if "lugar_elegido" not in df.columns:

        raise ValueError(
            "La tabla dataset_entrenamiento "
            "debe tener la columna 'lugar_elegido'."
        )


    # ----------------------------------------
    # Limpiar APTO
    # ----------------------------------------

    df = df.dropna(
        subset=["apto"]
    )

    df["apto"] = (
        df["apto"]
        .astype(int)
    )


    # ----------------------------------------
    # Limpiar lugar elegido
    # ----------------------------------------

    df["lugar_elegido"] = (
        df["lugar_elegido"]
        .fillna("No responde")
        .astype(str)
        .str.strip()
    )


    df = df[
        df["lugar_elegido"] != "No responde"
    ]


    # ----------------------------------------
    # Mostrar resumen
    # ----------------------------------------

    print("\n" + "=" * 60)
    print("RESUMEN DEL DATASET")
    print("=" * 60)

    print(
        f"Total de registros válidos: {len(df)}"
    )

    print("\nDistribución APTO:")

    print(
        df["apto"]
        .value_counts()
        .sort_index()
    )

    print("\nDistribución LUGAR ELEGIDO:")

    print(
        df["lugar_elegido"]
        .value_counts()
    )


    return df


# ============================================================
# CREAR PIPELINE
# ============================================================

def crear_pipeline() -> Pipeline:

    preprocesador = ColumnTransformer(
        transformers=[
            (
                "categoricas",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                COLUMNAS_ENTRADA
            )
        ]
    )


    modelo = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )


    pipeline = Pipeline(
        steps=[
            (
                "preprocesador",
                preprocesador
            ),
            (
                "modelo",
                modelo
            )
        ]
    )


    return pipeline


# ============================================================
# MODELO DE RESTRICCIONES
# ============================================================

def entrenar_modelo_restricciones(
    df: pd.DataFrame
) -> None:

    print("\n" + "=" * 60)
    print("ENTRENANDO MODELO DE RESTRICCIONES")
    print("=" * 60)


    X = df[COLUMNAS_ENTRADA]

    y = df["apto"]


    if y.nunique() < 2:

        raise ValueError(
            "La columna 'apto' debe contener "
            "como mínimo valores 0 y 1."
        )


    print("\nDistribución de clases:")

    print(
        y.value_counts()
        .sort_index()
    )


    # ----------------------------------------
    # División entrenamiento / prueba
    # ----------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y
        )
    )


    print(
        f"\nRegistros entrenamiento: {len(X_train)}"
    )

    print(
        f"Registros prueba: {len(X_test)}"
    )


    # ----------------------------------------
    # Entrenamiento
    # ----------------------------------------

    modelo = crear_pipeline()

    modelo.fit(
        X_train,
        y_train
    )


    # ----------------------------------------
    # Evaluación
    # ----------------------------------------

    predicciones = modelo.predict(
        X_test
    )


    exactitud = accuracy_score(
        y_test,
        predicciones
    )


    print(
        "\nExactitud modelo de restricciones:",
        round(exactitud, 4)
    )


    print("\nReporte de clasificación:")

    print(
        classification_report(
            y_test,
            predicciones,
            zero_division=0
        )
    )


    # ----------------------------------------
    # Guardar modelo
    # ----------------------------------------

    RUTA_MODELOS.mkdir(
        parents=True,
        exist_ok=True
    )


    ruta_modelo = (
        RUTA_MODELOS
        / "modelo_restricciones.pkl"
    )


    joblib.dump(
        modelo,
        ruta_modelo
    )


    print(
        "\nModelo de restricciones guardado en:"
    )

    print(
        ruta_modelo
    )


# ============================================================
# MODELO DE RECOMENDACIÓN
# ============================================================

def entrenar_modelo_recomendacion(
    df: pd.DataFrame
) -> None:

    print("\n" + "=" * 60)
    print("ENTRENANDO MODELO DE RECOMENDACIÓN")
    print("=" * 60)


    # Para recomendación usamos solamente
    # registros considerados aptos.
    df_apto = (
        df[
            df["apto"] == 1
        ]
        .copy()
    )


    print(
        "\nRegistros aptos disponibles:",
        len(df_apto)
    )


    if df_apto.empty:

        raise ValueError(
            "No existen registros con apto = 1."
        )


    X = df_apto[
        COLUMNAS_ENTRADA
    ]


    y = df_apto[
        "lugar_elegido"
    ]


    if y.nunique() < 2:

        raise ValueError(
            "La columna 'lugar_elegido' "
            "debe contener al menos "
            "dos lugares diferentes."
        )


    print("\nDistribución por lugar:")

    print(
        y.value_counts()
    )


    # ----------------------------------------
    # Validación para usar STRATIFY
    # ----------------------------------------

    conteo_clases = y.value_counts()


    if conteo_clases.min() < 2:

        print(
            "\nADVERTENCIA:"
            " Algún lugar tiene menos de 2 registros."
        )

        print(
            "La división se realizará sin stratify."
        )

        stratify_value = None

    else:

        stratify_value = y


    # ----------------------------------------
    # División entrenamiento / prueba
    # ----------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=stratify_value
        )
    )


    print(
        f"\nRegistros entrenamiento: {len(X_train)}"
    )

    print(
        f"Registros prueba: {len(X_test)}"
    )


    # ----------------------------------------
    # Entrenamiento
    # ----------------------------------------

    modelo = crear_pipeline()


    modelo.fit(
        X_train,
        y_train
    )


    # ----------------------------------------
    # Evaluación
    # ----------------------------------------

    predicciones = modelo.predict(
        X_test
    )


    exactitud = accuracy_score(
        y_test,
        predicciones
    )


    print(
        "\nExactitud modelo de recomendación:",
        round(exactitud, 4)
    )


    print("\nReporte de clasificación:")

    print(
        classification_report(
            y_test,
            predicciones,
            zero_division=0
        )
    )


    # ----------------------------------------
    # Guardar modelo
    # ----------------------------------------

    RUTA_MODELOS.mkdir(
        parents=True,
        exist_ok=True
    )


    ruta_modelo = (
        RUTA_MODELOS
        / "modelo_recomendacion.pkl"
    )


    joblib.dump(
        modelo,
        ruta_modelo
    )


    print(
        "\nModelo de recomendación guardado en:"
    )

    print(
        ruta_modelo
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 60)
    print("APP TURISMO")
    print("ENTRENAMIENTO DE MODELOS ML")
    print("=" * 60)


    # ----------------------------------------
    # 1. Obtener dataset desde Supabase
    # ----------------------------------------

    df = cargar_dataset_desde_supabase()


    # ----------------------------------------
    # 2. Limpiar dataset
    # ----------------------------------------

    df = limpiar_datos(df)


    # ----------------------------------------
    # 3. Entrenar restricciones
    # ----------------------------------------

    entrenar_modelo_restricciones(
        df
    )


    # ----------------------------------------
    # 4. Entrenar recomendación
    # ----------------------------------------

    entrenar_modelo_recomendacion(
        df
    )


    print("\n" + "=" * 60)
    print("ENTRENAMIENTO FINALIZADO CORRECTAMENTE")
    print("=" * 60)

    print(
        "\nLos dos modelos fueron generados:"
    )

    print(
        "- modelo_restricciones.pkl"
    )

    print(
        "- modelo_recomendacion.pkl"
    )

    print()


if __name__ == "__main__":
    main()