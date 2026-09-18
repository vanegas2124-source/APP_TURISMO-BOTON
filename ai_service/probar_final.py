from pprint import pprint

from app.ml_turismo.modelo_final import (
    obtener_resultado_final
)


solicitud = {

    "perfil_usuario": {

        "usuario_id":
            "usuario_001",

        "edad":
            "26-35",

        "compania": [
            "Pareja"
        ],

        "condicion_fisica":
            "Media",

        "discapacidad_fisica":
            "No",

        "enfermedad":
            "Ninguna"
    },


    "preferencias_actuales": {

        "actividades_preferidas": [
            "fotografia de paisajes",
            "relajacion y descanso"
        ],

        "gusto_naturaleza":
            "mucho",

        "gusto_aventura":
            "poco",

        "importancia_seguridad":
            "alta",

        "distancia":
            20,

        "duracion":
            "1 a 3 horas",

        "presupuesto":
            "$20.000 – $50.000",

        "acepta_lluvia":
            "No",

        "clima_preferido":
            "soleado",

        "riesgo_aceptado":
            "bajo",

        "riesgos_preocupantes": [
            "Clima (lluvia, tormentas)",
            "Terreno difícil (lodo, pendientes)"
        ]
    },


    "ubicacion_actual": {

        "latitud":
            4.1420,

        "longitud":
            -73.6266
    }
}


resultado = obtener_resultado_final(
    solicitud
)


pprint(
    resultado,
    sort_dicts=False
)