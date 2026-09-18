# ============================================================
# router.py
# APP TURISMO - API DEL MÓDULO MACHINE LEARNING
#
# Endpoints:
#   POST /v1/ml/modelo-restricciones
#   POST /v1/ml/modelo-recomendacion
#   POST /v1/ml/recomendar
#   GET  /v1/ml/health
# ============================================================

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


from .modelo_final import (
    obtener_lugares_aptos_por_restricciones,
    obtener_recomendacion_enriquecida,
    obtener_resultado_final,
)


router = APIRouter(
    prefix="/v1/ml",
    tags=["Machine Learning Turismo"]
)


# ============================================================
# MODELOS DE ENTRADA
# ============================================================

class PerfilUsuario(BaseModel):

    usuario_id: Optional[str] = None

    edad: str

    compania: List[str] = Field(
        default_factory=list
    )

    condicion_fisica: str

    discapacidad_fisica: str

    enfermedad: str


class PreferenciasActuales(BaseModel):

    actividades_preferidas: List[str] = Field(
        default_factory=list
    )

    gusto_naturaleza: str

    gusto_aventura: str

    importancia_seguridad: str

    distancia: float

    duracion: str

    presupuesto: str

    acepta_lluvia: str

    clima_preferido: str

    riesgo_aceptado: str

    riesgos_preocupantes: List[str] = Field(
        default_factory=list
    )


class UbicacionActual(BaseModel):

    latitud: float

    longitud: float


class SolicitudML(BaseModel):

    perfil_usuario: PerfilUsuario

    preferencias_actuales: PreferenciasActuales

    ubicacion_actual: UbicacionActual


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def health_ml():

    return {
        "status": "ok",
        "modulo": "machine_learning_turismo",
        "modelos": [
            "restricciones",
            "recomendacion",
            "final"
        ]
    }


# ============================================================
# 1. MODELO DE RESTRICCIONES
# ============================================================

@router.post("/modelo-restricciones")
def modelo_restricciones(
    payload: SolicitudML
):

    try:

        solicitud = payload.model_dump()

        resultado = (
            obtener_lugares_aptos_por_restricciones(
                solicitud=solicitud,
                top_n=3
            )
        )

        return {
            "modelo": "restricciones",
            **resultado
        }


    except FileNotFoundError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error ejecutando el modelo "
                f"de restricciones: {error}"
            )
        )


# ============================================================
# 2. MODELO DE RECOMENDACIÓN
# ============================================================

@router.post("/modelo-recomendacion")
def modelo_recomendacion(
    payload: SolicitudML
):

    try:

        solicitud = payload.model_dump()

        resultado = (
            obtener_recomendacion_enriquecida(
                solicitud=solicitud,
                top_n=3
            )
        )

        return resultado


    except FileNotFoundError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error ejecutando el modelo "
                f"de recomendación: {error}"
            )
        )


# ============================================================
# 3. MODELO FINAL
# ============================================================

@router.post("/recomendar")
def modelo_final(
    payload: SolicitudML
):

    try:

        solicitud = payload.model_dump()

        resultado = obtener_resultado_final(
            solicitud
        )

        return resultado


    except FileNotFoundError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error ejecutando el modelo final: "
                f"{error}"
            )
        )