import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client


# APP_TURISMO-BOTON/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = (
    os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("SUPABASE_PUBLISHABLE_KEY")
)


if not SUPABASE_URL:
    raise RuntimeError(
        "No se encontró SUPABASE_URL en el .env"
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "No se encontró SUPABASE_ANON_KEY "
        "ni SUPABASE_PUBLISHABLE_KEY en el .env"
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)
# ============================================================
# CONSULTAS DEL MÓDULO ML
# ============================================================


def obtener_lugares():
    """
    Obtiene todos los lugares turísticos almacenados
    en la tabla public.lugares de Supabase.
    """

    respuesta = (
        supabase
        .table("lugares")
        .select("*")
        .order("id")
        .execute()
    )

    return respuesta.data or []


def obtener_lugar_por_nombre(nombre: str):
    """
    Busca un lugar turístico por su nombre.
    """

    respuesta = (
        supabase
        .table("lugares")
        .select("*")
        .eq("nombre", nombre)
        .limit(1)
        .execute()
    )

    datos = respuesta.data or []

    if not datos:
        return None

    return datos[0]