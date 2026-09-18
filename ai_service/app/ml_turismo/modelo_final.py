# ============================================================
# modelo_final.py
# APP TURISMO
#
# Combina:
#   1. Modelo ML de restricciones
#   2. Modelo ML de recomendación
#   3. Reglas reales de los lugares
#   4. Distancia geográfica
#   5. Información almacenada en Supabase
#
# Resultado:
#   Top 3 final de lugares turísticos
# ============================================================

import re
import unicodedata

from typing import Any, Dict, List, Optional


from .modelo_ml_restricciones import (
    predecir_restriccion
)

from .modelo_ml_recomendacion import (
    recomendar_lugar
)

from .supabase_ml import (
    obtener_lugares
)

from .utils_distancia import (
    calcular_distancia_km
)


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def normalizar_texto(
    texto: Any
) -> str:
    """
    Convierte un texto a minúsculas y elimina tildes.

    Ejemplo:
        "Sí" -> "si"
        "Condición Física" -> "condicion fisica"
    """

    if texto is None:
        return ""

    texto = str(
        texto
    ).strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

    return texto


def valor_valido(
    valor: Any
) -> bool:

    return (
        valor is not None
        and valor != ""
    )


def convertir_a_float(
    valor: Any
) -> Optional[float]:
    """
    Convierte valores recibidos desde Supabase
    a float de forma segura.
    """

    if valor is None:
        return None

    try:
        return float(
            valor
        )

    except (
        TypeError,
        ValueError
    ):
        return None


# ============================================================
# UNIR DATOS DEL USUARIO
# ============================================================

def unir_datos_usuario(
    solicitud: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Une perfil_usuario y preferencias_actuales
    para enviarlos a los modelos ML.
    """

    perfil = (
        solicitud
        .get(
            "perfil_usuario",
            {}
        )
        .copy()
    )

    preferencias = (
        solicitud
        .get(
            "preferencias_actuales",
            {}
        )
        .copy()
    )

    # usuario_id no fue utilizado como variable
    # durante el entrenamiento.
    perfil.pop(
        "usuario_id",
        None
    )

    return {
        **perfil,
        **preferencias
    }


# ============================================================
# DATOS BÁSICOS DEL LUGAR
# ============================================================

def obtener_datos_basicos_lugar(
    lugar: Dict[str, Any]
) -> Dict[str, Any]:

    return {

        "id":
            lugar.get("id"),

        "nombre":
            lugar.get("nombre"),

        "vereda":
            lugar.get("vereda"),

        "tipo_turismo":
            lugar.get(
                "tipo_turismo"
            ),

        "nivel_riesgo":
            lugar.get(
                "nivel_riesgo"
            ),

        "nivel_esfuerzo":
            lugar.get(
                "nivel_esfuerzo"
            ),

        "clima_recomendado":
            lugar.get(
                "clima_recomendado"
            ),

        "presupuesto_aprox":
            lugar.get(
                "presupuesto_aprox"
            ),

        "duracion_aprox":
            lugar.get(
                "duracion_aprox"
            ),

        "descripcion":
            lugar.get(
                "descripcion"
            ),

        "latitud":
            convertir_a_float(
                lugar.get(
                    "latitud"
                )
            ),

        "longitud":
            convertir_a_float(
                lugar.get(
                    "longitud"
                )
            )
    }


# ============================================================
# EDAD
# ============================================================

def convertir_edad_a_numero(
    edad: str
) -> int:
    """
    Convierte rangos del formulario en un número
    aproximado para evaluar restricciones.

    Se conserva el comportamiento del proyecto original.
    """

    edad_texto = normalizar_texto(
        edad
    )

    numeros = re.findall(
        r"\d+",
        edad_texto
    )

    if numeros:
        return int(
            numeros[-1]
        )

    if "mayor" in edad_texto:
        return 65

    return 30


# ============================================================
# NIVELES BAJO / MEDIO / ALTO
# ============================================================

def nivel_a_numero(
    nivel: Any
) -> int:

    nivel = normalizar_texto(
        nivel
    )

    if nivel in [
        "bajo",
        "baja",
        "minimo",
        "minima"
    ]:
        return 1

    if nivel in [
        "medio",
        "media",
        "moderado",
        "moderada"
    ]:
        return 2

    if nivel in [
        "alto",
        "alta",
        "elevado",
        "elevada"
    ]:
        return 3

    # Valor neutro cuando no se reconoce.
    return 2


def numero_a_nivel(
    numero: int
) -> str:

    if numero <= 1:
        return "bajo"

    if numero == 2:
        return "medio"

    return "alto"


# ============================================================
# PRESUPUESTO Y DURACIÓN
# ============================================================

def extraer_numeros_de_texto(
    texto: Any
) -> List[int]:

    if texto is None:
        return []

    texto = str(
        texto
    )

    numeros = re.findall(
        r"\d[\d\.\,]*",
        texto
    )

    valores = []

    for numero in numeros:

        numero_limpio = (
            numero
            .replace(".", "")
            .replace(",", "")
        )

        try:
            valores.append(
                int(
                    numero_limpio
                )
            )

        except (
            TypeError,
            ValueError
        ):
            pass

    return valores


def obtener_monto_maximo_presupuesto(
    texto: Any
) -> Optional[int]:

    texto_normalizado = (
        normalizar_texto(
            texto
        )
    )

    if (
        "gratis"
        in texto_normalizado
        or
        "sin costo"
        in texto_normalizado
    ):
        return 0

    valores = (
        extraer_numeros_de_texto(
            texto
        )
    )

    if not valores:
        return None

    return max(
        valores
    )


def obtener_horas_maximas(
    texto: Any
) -> Optional[float]:

    texto_normalizado = (
        normalizar_texto(
            texto
        )
    )

    if not texto_normalizado:
        return None

    if (
        "menos de una hora"
        in texto_normalizado
    ):
        return 1.0

    if (
        "menos de 1 hora"
        in texto_normalizado
    ):
        return 1.0

    if (
        "media hora"
        in texto_normalizado
    ):
        return 0.5

    if (
        "una hora"
        in texto_normalizado
    ):
        return 1.0

    if (
        "todo el dia"
        in texto_normalizado
    ):
        return 12.0

    valores = (
        extraer_numeros_de_texto(
            texto
        )
    )

    if not valores:
        return None

    if (
        "minuto"
        in texto_normalizado
    ):
        return (
            float(
                max(valores)
            )
            / 60
        )

    return float(
        max(valores)
    )


# ============================================================
# DISTANCIA
# ============================================================

def calcular_distancia_lugar(
    solicitud: Dict[str, Any],
    lugar: Dict[str, Any]
) -> Optional[float]:

    ubicacion = solicitud.get(
        "ubicacion_actual",
        {}
    )

    latitud_usuario = (
        convertir_a_float(
            ubicacion.get(
                "latitud"
            )
        )
    )

    longitud_usuario = (
        convertir_a_float(
            ubicacion.get(
                "longitud"
            )
        )
    )

    latitud_lugar = (
        convertir_a_float(
            lugar.get(
                "latitud"
            )
        )
    )

    longitud_lugar = (
        convertir_a_float(
            lugar.get(
                "longitud"
            )
        )
    )

    if (
        latitud_usuario is None
        or longitud_usuario is None
        or latitud_lugar is None
        or longitud_lugar is None
    ):
        return None

    return calcular_distancia_km(
        latitud_usuario,
        longitud_usuario,
        latitud_lugar,
        longitud_lugar
    )


# ============================================================
# REGLAS REALES DE RESTRICCIÓN DEL LUGAR
# ============================================================

def validar_lugar_con_restricciones(
    solicitud: Dict[str, Any],
    lugar: Dict[str, Any],
    distancia_km: Optional[float]
) -> Dict[str, Any]:

    perfil = solicitud.get(
        "perfil_usuario",
        {}
    )

    preferencias = solicitud.get(
        "preferencias_actuales",
        {}
    )


    # --------------------------------------------------------
    # Datos del usuario
    # --------------------------------------------------------

    edad_numero = (
        convertir_edad_a_numero(
            perfil.get(
                "edad",
                ""
            )
        )
    )

    condicion_fisica = (
        normalizar_texto(
            perfil.get(
                "condicion_fisica"
            )
        )
    )

    discapacidad = (
        normalizar_texto(
            perfil.get(
                "discapacidad_fisica"
            )
        )
    )

    enfermedad = (
        normalizar_texto(
            perfil.get(
                "enfermedad"
            )
        )
    )

    riesgo_aceptado_usuario = (
        nivel_a_numero(
            preferencias.get(
                "riesgo_aceptado"
            )
        )
    )

    seguridad_usuario = (
        nivel_a_numero(
            preferencias.get(
                "importancia_seguridad"
            )
        )
    )

    acepta_lluvia = (
        normalizar_texto(
            preferencias.get(
                "acepta_lluvia"
            )
        )
    )

    clima_preferido_usuario = (
        normalizar_texto(
            preferencias.get(
                "clima_preferido"
            )
        )
    )


    # --------------------------------------------------------
    # Datos del lugar
    # --------------------------------------------------------

    nivel_riesgo_lugar = (
        nivel_a_numero(
            lugar.get(
                "nivel_riesgo"
            )
        )
    )

    nivel_esfuerzo_lugar = (
        nivel_a_numero(
            lugar.get(
                "nivel_esfuerzo"
            )
        )
    )

    clima_lugar = (
        normalizar_texto(
            lugar.get(
                "clima_recomendado"
            )
        )
    )

    tipo_turismo = (
        normalizar_texto(
            lugar.get(
                "tipo_turismo"
            )
        )
    )

    nombre_lugar = (
        normalizar_texto(
            lugar.get(
                "nombre"
            )
        )
    )


    # --------------------------------------------------------
    # Presupuesto
    # --------------------------------------------------------

    presupuesto_usuario_max = (
        obtener_monto_maximo_presupuesto(
            preferencias.get(
                "presupuesto"
            )
        )
    )

    presupuesto_lugar_max = (
        obtener_monto_maximo_presupuesto(
            lugar.get(
                "presupuesto_aprox"
            )
        )
    )


    # --------------------------------------------------------
    # Duración
    # --------------------------------------------------------

    duracion_usuario_max = (
        obtener_horas_maximas(
            preferencias.get(
                "duracion"
            )
        )
    )

    duracion_lugar_max = (
        obtener_horas_maximas(
            lugar.get(
                "duracion_aprox"
            )
        )
    )


    razones = []
    advertencias = []


    # --------------------------------------------------------
    # Distancia máxima
    # --------------------------------------------------------

    distancia_maxima = (
        convertir_a_float(
            preferencias.get(
                "distancia"
            )
        )
    )

    if (
        distancia_km is not None
        and distancia_maxima is not None
        and distancia_km
        > distancia_maxima
    ):

        razones.append(
            "El lugar supera la distancia máxima "
            "indicada por el usuario."
        )


    # --------------------------------------------------------
    # Riesgo
    # --------------------------------------------------------

    if (
        nivel_riesgo_lugar
        > riesgo_aceptado_usuario
    ):

        razones.append(
            "El lugar tiene riesgo "
            f"{numero_a_nivel(nivel_riesgo_lugar)} "
            "y el usuario acepta riesgo "
            f"{numero_a_nivel(riesgo_aceptado_usuario)}."
        )


    if (
        seguridad_usuario == 3
        and nivel_riesgo_lugar == 3
    ):

        razones.append(
            "El usuario prioriza alta seguridad "
            "y el lugar es de alto riesgo."
        )


    # --------------------------------------------------------
    # Edad
    # --------------------------------------------------------

    if (
        edad_numero >= 60
        and nivel_riesgo_lugar == 3
    ):

        razones.append(
            "No se recomienda una actividad de alto "
            "riesgo para un adulto mayor."
        )


    if (
        edad_numero >= 70
        and nivel_riesgo_lugar >= 2
    ):

        razones.append(
            "Para una persona de 70 años o más "
            "se priorizan lugares de bajo riesgo."
        )


    if (
        edad_numero >= 60
        and nivel_esfuerzo_lugar == 3
    ):

        razones.append(
            "El lugar exige alto esfuerzo físico "
            "y el usuario es adulto mayor."
        )


    # --------------------------------------------------------
    # Condición física
    # --------------------------------------------------------

    if (
        condicion_fisica == "baja"
        and nivel_esfuerzo_lugar >= 2
    ):

        razones.append(
            "El usuario tiene condición física baja "
            "y el lugar exige esfuerzo medio o alto."
        )


    if (
        condicion_fisica == "media"
        and edad_numero >= 70
        and nivel_esfuerzo_lugar >= 2
    ):

        razones.append(
            "El usuario es adulto mayor y el lugar "
            "exige esfuerzo medio o alto."
        )


    # --------------------------------------------------------
    # Discapacidad
    # --------------------------------------------------------

    if (
        discapacidad in [
            "si",
            "sí"
        ]
        and nivel_esfuerzo_lugar >= 2
    ):

        razones.append(
            "El usuario reporta discapacidad física "
            "y el lugar puede requerir esfuerzo "
            "o movilidad."
        )


    # --------------------------------------------------------
    # Enfermedad
    # --------------------------------------------------------

    if enfermedad not in [
        "ninguna",
        "no",
        "sin enfermedad",
        ""
    ]:

        if (
            nivel_riesgo_lugar >= 2
            or nivel_esfuerzo_lugar >= 2
        ):

            razones.append(
                "El usuario reporta enfermedad y el "
                "lugar tiene riesgo o esfuerzo "
                "medio/alto."
            )


    # --------------------------------------------------------
    # Lluvia
    # --------------------------------------------------------

    if (
        acepta_lluvia
        in [
            "no",
            "n"
        ]
        and (
            "lluvia"
            in clima_lugar
            or
            "lluvioso"
            in clima_lugar
        )
    ):

        razones.append(
            "El usuario no acepta lluvia y el lugar "
            "se recomienda en clima lluvioso."
        )


    # --------------------------------------------------------
    # Presupuesto
    # --------------------------------------------------------

    if (
        presupuesto_usuario_max
        is not None
        and presupuesto_lugar_max
        is not None
    ):

        if (
            presupuesto_lugar_max
            > presupuesto_usuario_max
        ):

            razones.append(
                "El presupuesto aproximado del lugar "
                "supera el presupuesto del usuario."
            )


    # --------------------------------------------------------
    # Duración
    # --------------------------------------------------------

    if (
        duracion_usuario_max
        is not None
        and duracion_lugar_max
        is not None
    ):

        if (
            duracion_lugar_max
            > duracion_usuario_max
        ):

            razones.append(
                "La duración aproximada del lugar "
                "supera el tiempo disponible del usuario."
            )


    # --------------------------------------------------------
    # Actividades extremas
    # --------------------------------------------------------

    palabras_alto_riesgo = [
        "parapente",
        "lanzadero",
        "canopy",
        "rafting",
        "torrentismo",
        "rapel",
        "escalada",
        "extremo",
        "altura",
        "vuelo",
        "volar",
        "salto"
    ]


    texto_lugar = (
        f"{nombre_lugar} "
        f"{tipo_turismo}"
    )


    if any(
        palabra in texto_lugar
        for palabra
        in palabras_alto_riesgo
    ):

        if (
            riesgo_aceptado_usuario
            <= 2
        ):

            razones.append(
                "El lugar corresponde a una actividad "
                "extrema o de altura y el usuario "
                "no acepta alto riesgo."
            )

        if edad_numero >= 60:

            razones.append(
                "La actividad extrema o de altura "
                "no se recomienda para un adulto mayor."
            )


    # --------------------------------------------------------
    # Preferencia climática
    # --------------------------------------------------------

    if (
        clima_preferido_usuario
        and clima_lugar
    ):

        if (
            clima_preferido_usuario
            not in clima_lugar
            and
            clima_lugar
            not in clima_preferido_usuario
        ):

            advertencias.append(
                "El clima recomendado del lugar "
                "no coincide totalmente con el clima "
                "preferido del usuario."
            )


    return {

        "apto_por_reglas":
            len(razones) == 0,

        "nivel_riesgo_lugar":
            numero_a_nivel(
                nivel_riesgo_lugar
            ),

        "nivel_esfuerzo_lugar":
            numero_a_nivel(
                nivel_esfuerzo_lugar
            ),

        "razones_bloqueo":
            razones,

        "advertencias":
            advertencias
    }


# ============================================================
# PUNTAJE DEL MODELO DE RESTRICCIONES
# ============================================================

def calcular_puntaje_restricciones(
    probabilidad_apto: float,
    distancia_km: Optional[float],
    nivel_riesgo_lugar: str,
    nivel_esfuerzo_lugar: str
) -> float:

    puntaje = (
        probabilidad_apto
        * 100
    )


    riesgo_numero = (
        nivel_a_numero(
            nivel_riesgo_lugar
        )
    )


    esfuerzo_numero = (
        nivel_a_numero(
            nivel_esfuerzo_lugar
        )
    )


    # Penalización por riesgo
    puntaje -= (
        riesgo_numero - 1
    ) * 12


    # Penalización por esfuerzo
    puntaje -= (
        esfuerzo_numero - 1
    ) * 8


    # Penalización por distancia
    if distancia_km is not None:

        puntaje -= (
            min(
                distancia_km,
                100
            )
            * 0.2
        )


    return round(
        puntaje,
        2
    )


# ============================================================
# EXPLICACIÓN SI NO HAY LUGARES
# ============================================================

def generar_explicacion_sin_resultados(
    lugares_descartados: List[
        Dict[str, Any]
    ]
) -> Dict[str, Any]:

    if not lugares_descartados:

        return {

            "resumen":
                "No se encontraron lugares aptos "
                "y no hay información suficiente "
                "para explicar el motivo.",

            "causas_principales":
                [],

            "sugerencias": [
                "Verifica que existan lugares "
                "registrados en Supabase.",
                "Verifica que los lugares tengan "
                "riesgo, esfuerzo, duración, "
                "presupuesto y coordenadas."
            ]
        }


    conteo_razones = {}
    ejemplos_por_razon = {}


    for lugar in lugares_descartados:

        razones = lugar.get(
            "razones_bloqueo",
            []
        )

        for razon in razones:

            conteo_razones[razon] = (
                conteo_razones.get(
                    razon,
                    0
                )
                + 1
            )

            ejemplos_por_razon.setdefault(
                razon,
                []
            )

            ejemplos_por_razon[
                razon
            ].append(
                lugar.get(
                    "lugar"
                )
            )


    causas_principales = []


    for razon, cantidad in sorted(
        conteo_razones.items(),
        key=lambda item:
            item[1],
        reverse=True
    ):

        causas_principales.append(
            {
                "razon":
                    razon,

                "cantidad_lugares_afectados":
                    cantidad,

                "ejemplos_lugares":
                    ejemplos_por_razon.get(
                        razon,
                        []
                    )[:3]
            }
        )


    texto_razones = (
        " ".join(
            conteo_razones.keys()
        )
        .lower()
    )


    sugerencias = []


    if (
        "distancia máxima"
        in texto_razones
    ):

        sugerencias.append(
            "Aumentar la distancia máxima permitida."
        )


    if (
        "riesgo"
        in texto_razones
    ):

        sugerencias.append(
            "Seleccionar un nivel de riesgo compatible "
            "con las capacidades reales del turista."
        )


    if (
        "adulto mayor"
        in texto_razones
        or
        "70 años"
        in texto_razones
    ):

        sugerencias.append(
            "Priorizar lugares de bajo riesgo y "
            "bajo esfuerzo físico."
        )


    if (
        "esfuerzo"
        in texto_razones
        or
        "condición física"
        in texto_razones
    ):

        sugerencias.append(
            "Seleccionar actividades de menor "
            "exigencia física."
        )


    if (
        "presupuesto"
        in texto_razones
    ):

        sugerencias.append(
            "Seleccionar lugares con menor costo "
            "o ampliar el presupuesto disponible."
        )


    if (
        "duración"
        in texto_razones
        or
        "tiempo disponible"
        in texto_razones
    ):

        sugerencias.append(
            "Seleccionar actividades de menor duración."
        )


    if (
        "lluvia"
        in texto_razones
        or
        "clima"
        in texto_razones
    ):

        sugerencias.append(
            "Seleccionar lugares compatibles "
            "con la preferencia climática."
        )


    if (
        "no apto"
        in texto_razones
    ):

        sugerencias.append(
            "El modelo clasificó algunos lugares "
            "como no aptos para este perfil."
        )


    if not sugerencias:

        sugerencias.append(
            "Revisar las preferencias del turista "
            "y la información registrada de los lugares."
        )


    return {

        "resumen":
            f"Se evaluaron "
            f"{len(lugares_descartados)} lugares, "
            "pero ninguno cumplió las restricciones "
            "necesarias.",

        "causas_principales":
            causas_principales,

        "sugerencias":
            sugerencias
    }


# ============================================================
# MODELO DE RESTRICCIONES POR CADA LUGAR
# ============================================================

def obtener_lugares_aptos_por_restricciones(
    solicitud: Dict[str, Any],
    top_n: Optional[int] = 3
) -> Dict[str, Any]:

    datos_base_usuario = (
        unir_datos_usuario(
            solicitud
        )
    )


    # --------------------------------------------------------
    # Leer lugares desde Supabase
    # --------------------------------------------------------

    lugares = obtener_lugares()


    lugares_aptos = []

    lugares_descartados = []


    # --------------------------------------------------------
    # Evaluar cada lugar
    # --------------------------------------------------------

    for lugar in lugares:

        nombre_lugar = (
            lugar.get(
                "nombre"
            )
        )


        distancia_km = (
            calcular_distancia_lugar(
                solicitud,
                lugar
            )
        )


        # ----------------------------------------------------
        # Reglas reales
        # ----------------------------------------------------

        validacion = (
            validar_lugar_con_restricciones(
                solicitud,
                lugar,
                distancia_km
            )
        )


        if not validacion[
            "apto_por_reglas"
        ]:

            lugares_descartados.append(
                {
                    "lugar":
                        nombre_lugar,

                    "nivel_riesgo_lugar":
                        validacion[
                            "nivel_riesgo_lugar"
                        ],

                    "nivel_esfuerzo_lugar":
                        validacion[
                            "nivel_esfuerzo_lugar"
                        ],

                    "distancia_km":
                        distancia_km,

                    "razones_bloqueo":
                        validacion[
                            "razones_bloqueo"
                        ],

                    "datos_lugar":
                        obtener_datos_basicos_lugar(
                            lugar
                        )
                }
            )

            continue


        # ----------------------------------------------------
        # Evaluación ML para este lugar
        # ----------------------------------------------------

        datos_usuario_para_lugar = (
            datos_base_usuario.copy()
        )


        if distancia_km is not None:

            datos_usuario_para_lugar[
                "distancia"
            ] = distancia_km


        resultado_ml = (
            predecir_restriccion(
                datos_usuario_para_lugar
            )
        )


        probabilidad_apto = (
            resultado_ml.get(
                "probabilidad_apto"
            )
        )


        if probabilidad_apto is None:

            probabilidad_apto = (
                1.0
                if resultado_ml.get(
                    "apto"
                )
                else 0.0
            )


        # ----------------------------------------------------
        # Si ML también considera apto
        # ----------------------------------------------------

        if resultado_ml.get(
            "apto"
        ):

            puntaje = (
                calcular_puntaje_restricciones(
                    probabilidad_apto=float(
                        probabilidad_apto
                    ),
                    distancia_km=distancia_km,
                    nivel_riesgo_lugar=(
                        validacion[
                            "nivel_riesgo_lugar"
                        ]
                    ),
                    nivel_esfuerzo_lugar=(
                        validacion[
                            "nivel_esfuerzo_lugar"
                        ]
                    )
                )
            )


            distancia_maxima = (
                solicitud
                .get(
                    "preferencias_actuales",
                    {}
                )
                .get(
                    "distancia"
                )
            )


            lugares_aptos.append(
                {
                    "lugar":
                        nombre_lugar,

                    "resultado_restriccion":
                        "APTO",

                    "probabilidad_apto":
                        round(
                            float(
                                probabilidad_apto
                            ),
                            4
                        ),

                    "puntaje_restricciones":
                        puntaje,

                    "nivel_riesgo_lugar":
                        validacion[
                            "nivel_riesgo_lugar"
                        ],

                    "nivel_esfuerzo_lugar":
                        validacion[
                            "nivel_esfuerzo_lugar"
                        ],

                    "distancia_km":
                        distancia_km,

                    "distancia_maxima_usuario_km":
                        distancia_maxima,

                    "dentro_distancia_maxima":
                        True,

                    "advertencias":
                        validacion[
                            "advertencias"
                        ],

                    "datos_lugar":
                        obtener_datos_basicos_lugar(
                            lugar
                        )
                }
            )


        # ----------------------------------------------------
        # ML lo considera NO APTO
        # ----------------------------------------------------

        else:

            lugares_descartados.append(
                {
                    "lugar":
                        nombre_lugar,

                    "nivel_riesgo_lugar":
                        validacion[
                            "nivel_riesgo_lugar"
                        ],

                    "nivel_esfuerzo_lugar":
                        validacion[
                            "nivel_esfuerzo_lugar"
                        ],

                    "distancia_km":
                        distancia_km,

                    "razones_bloqueo": [
                        "El modelo de restricciones "
                        "clasificó el lugar como NO APTO."
                    ],

                    "datos_lugar":
                        obtener_datos_basicos_lugar(
                            lugar
                        )
                }
            )


    # --------------------------------------------------------
    # Ordenar mejores lugares aptos
    # --------------------------------------------------------

    lugares_aptos = sorted(
        lugares_aptos,
        key=lambda item: (
            item[
                "puntaje_restricciones"
            ],
            item[
                "probabilidad_apto"
            ],
            -(
                item[
                    "distancia_km"
                ]
                if item[
                    "distancia_km"
                ]
                is not None
                else 999999
            )
        ),
        reverse=True
    )


    total_lugares_aptos = (
        len(
            lugares_aptos
        )
    )


    # --------------------------------------------------------
    # Limitar Top
    # --------------------------------------------------------

    if top_n is not None:

        lugares_aptos = (
            lugares_aptos[
                :top_n
            ]
        )


    for indice, item in enumerate(
        lugares_aptos,
        start=1
    ):

        item[
            "posicion"
        ] = indice


    # --------------------------------------------------------
    # Explicación si no hubo resultados
    # --------------------------------------------------------

    explicacion = None


    if (
        total_lugares_aptos
        == 0
    ):

        explicacion = (
            generar_explicacion_sin_resultados(
                lugares_descartados
            )
        )


    return {

        "total_lugares_aptos":
            total_lugares_aptos,

        "top_lugares_aptos":
            lugares_aptos,

        "lugares_descartados_por_restricciones":
            lugares_descartados,

        "explicacion_no_resultados":
            explicacion
    }


# ============================================================
# RECOMENDACIÓN + DATOS DE SUPABASE
# ============================================================

def obtener_recomendacion_enriquecida(
    solicitud: Dict[str, Any],
    top_n: int = 3
) -> Dict[str, Any]:

    datos_usuario = (
        unir_datos_usuario(
            solicitud
        )
    )


    # Ranking ML completo
    resultado = (
        recomendar_lugar(
            usuario=datos_usuario,
            top_n=None
        )
    )


    lugares = obtener_lugares()


    mapa_lugares = {

        normalizar_texto(
            lugar.get(
                "nombre"
            )
        ):
            lugar

        for lugar
        in lugares
    }


    ranking_original = (
        resultado.get(
            "ranking",
            []
        )
    )


    ranking_enriquecido = []


    for item in ranking_original:

        nombre_lugar = (
            item.get(
                "lugar"
            )
        )


        clave_lugar = (
            normalizar_texto(
                nombre_lugar
            )
        )


        lugar_bd = (
            mapa_lugares.get(
                clave_lugar
            )
        )


        distancia_km = None

        dentro_distancia = None

        datos_lugar = None

        validacion = None


        if lugar_bd:

            distancia_km = (
                calcular_distancia_lugar(
                    solicitud,
                    lugar_bd
                )
            )


            distancia_maxima = (
                solicitud
                .get(
                    "preferencias_actuales",
                    {}
                )
                .get(
                    "distancia"
                )
            )


            if (
                distancia_km is not None
                and distancia_maxima is not None
            ):

                dentro_distancia = (
                    distancia_km
                    <= float(
                        distancia_maxima
                    )
                )


            datos_lugar = (
                obtener_datos_basicos_lugar(
                    lugar_bd
                )
            )


            validacion = (
                validar_lugar_con_restricciones(
                    solicitud,
                    lugar_bd,
                    distancia_km
                )
            )


        ranking_enriquecido.append(
            {
                **item,

                "distancia_km":
                    distancia_km,

                "distancia_maxima_usuario_km":
                    solicitud
                    .get(
                        "preferencias_actuales",
                        {}
                    )
                    .get(
                        "distancia"
                    ),

                "dentro_distancia_maxima":
                    dentro_distancia,

                "apto_por_reglas":
                    (
                        validacion[
                            "apto_por_reglas"
                        ]
                        if validacion
                        else None
                    ),

                "razones_bloqueo":
                    (
                        validacion[
                            "razones_bloqueo"
                        ]
                        if validacion
                        else []
                    ),

                "datos_lugar":
                    datos_lugar
            }
        )


    ranking_enriquecido = (
        ranking_enriquecido[
            :top_n
        ]
    )


    for indice, item in enumerate(
        ranking_enriquecido,
        start=1
    ):

        item[
            "posicion"
        ] = indice


    return {

        "modelo":
            "recomendacion",

        "lugar_recomendado":
            (
                ranking_enriquecido[
                    0
                ][
                    "lugar"
                ]
                if ranking_enriquecido
                else None
            ),

        "top_3":
            ranking_enriquecido,

        "ranking":
            ranking_enriquecido
    }


# ============================================================
# MODELO FINAL
# ============================================================

def obtener_resultado_final(
    solicitud: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Flujo final:

        1. Evalúa restricciones reales
        2. Evalúa modelo ML de restricciones
        3. Obtiene lugares aptos
        4. Ejecuta modelo de recomendación
        5. Cruza ambos resultados
        6. Calcula puntaje final
        7. Devuelve Top 3
    """

    datos_usuario = (
        unir_datos_usuario(
            solicitud
        )
    )


    # ========================================================
    # 1. RESTRICCIONES
    # ========================================================

    resultado_restricciones = (
        obtener_lugares_aptos_por_restricciones(
            solicitud,
            top_n=None
        )
    )


    lugares_aptos = (
        resultado_restricciones[
            "top_lugares_aptos"
        ]
    )


    # ========================================================
    # NO HAY NINGÚN LUGAR APTO
    # ========================================================

    if not lugares_aptos:

        return {

            "estado":
                "no_recomendado",

            "mensaje":
                "No se encontraron lugares aptos "
                "según las restricciones del usuario.",

            "resultado_final": {

                "lugar_recomendado":
                    None,

                "top_3":
                    []
            },

            "explicacion_no_resultados":
                resultado_restricciones.get(
                    "explicacion_no_resultados"
                ),

            "datos_para_historial": {

                "apto":
                    False,

                "probabilidad_apto":
                    None,

                "lugar_recomendado":
                    None,

                "ranking":
                    []
            }
        }


    # ========================================================
    # MAPA DE LUGARES APTOS
    # ========================================================

    mapa_lugares_aptos = {

        normalizar_texto(
            item[
                "lugar"
            ]
        ):
            item

        for item
        in lugares_aptos
    }


    # ========================================================
    # 2. RECOMENDACIÓN
    # ========================================================

    resultado_recomendacion = (
        recomendar_lugar(
            usuario=datos_usuario,
            top_n=None
        )
    )


    ranking_recomendacion = (
        resultado_recomendacion.get(
            "ranking",
            []
        )
    )


    # ========================================================
    # 3. CRUCE RECOMENDACIÓN + RESTRICCIONES
    # ========================================================

    ranking_final = []


    for item in ranking_recomendacion:

        nombre_lugar = (
            item.get(
                "lugar"
            )
        )


        clave_lugar = (
            normalizar_texto(
                nombre_lugar
            )
        )


        # Solamente entran lugares que aprobaron
        # las restricciones.
        if (
            clave_lugar
            not in mapa_lugares_aptos
        ):
            continue


        datos_restriccion = (
            mapa_lugares_aptos[
                clave_lugar
            ]
        )


        prob_recomendacion = (
            item.get(
                "probabilidad"
            )
            or 0
        )


        prob_apto = (
            datos_restriccion.get(
                "probabilidad_apto"
            )
            or 0
        )


        puntaje_restricciones = (
            datos_restriccion.get(
                "puntaje_restricciones"
            )
            or 0
        )


        # ====================================================
        # FÓRMULA DEL MODELO FINAL
        # ====================================================
        #
        # Recomendación: 60 %
        # Aptitud ML:     25 %
        # Restricciones:  15 %
        #
        # El puntaje_restricciones ya está en escala 0-100.
        # ====================================================

        puntaje_final = round(
            (
                float(
                    prob_recomendacion
                )
                * 60
            )
            +
            (
                float(
                    prob_apto
                )
                * 25
            )
            +
            (
                float(
                    puntaje_restricciones
                )
                * 0.15
            ),
            2
        )


        ranking_final.append(
            {
                "lugar":
                    nombre_lugar,

                "puntaje_final":
                    puntaje_final,

                "probabilidad_recomendacion":
                    item.get(
                        "probabilidad"
                    ),

                "probabilidad_apto_restricciones":
                    datos_restriccion.get(
                        "probabilidad_apto"
                    ),

                "puntaje_restricciones":
                    datos_restriccion.get(
                        "puntaje_restricciones"
                    ),

                "nivel_riesgo_lugar":
                    datos_restriccion.get(
                        "nivel_riesgo_lugar"
                    ),

                "nivel_esfuerzo_lugar":
                    datos_restriccion.get(
                        "nivel_esfuerzo_lugar"
                    ),

                "distancia_km":
                    datos_restriccion.get(
                        "distancia_km"
                    ),

                "distancia_maxima_usuario_km":
                    datos_restriccion.get(
                        "distancia_maxima_usuario_km"
                    ),

                "dentro_distancia_maxima":
                    datos_restriccion.get(
                        "dentro_distancia_maxima"
                    ),

                "advertencias":
                    datos_restriccion.get(
                        "advertencias",
                        []
                    ),

                "datos_lugar":
                    datos_restriccion.get(
                        "datos_lugar"
                    )
            }
        )


    # ========================================================
    # 4. ORDENAR TOP FINAL
    # ========================================================

    ranking_final = sorted(
        ranking_final,
        key=lambda item:
            item[
                "puntaje_final"
            ],
        reverse=True
    )


    ranking_final = (
        ranking_final[:3]
    )


    for indice, item in enumerate(
        ranking_final,
        start=1
    ):

        item[
            "posicion"
        ] = indice


    # ========================================================
    # 5. FALLBACK
    #
    # Si recomendación y restricciones no coinciden,
    # entregamos los lugares más seguros según
    # restricciones.
    # ========================================================

    if not ranking_final:

        lugares_fallback = (
            lugares_aptos[:3]
        )


        for indice, item in enumerate(
            lugares_fallback,
            start=1
        ):

            item[
                "posicion"
            ] = indice


        lugar_fallback = (
            lugares_fallback[
                0
            ][
                "lugar"
            ]
            if lugares_fallback
            else None
        )


        return {

            "estado":
                "recomendado_por_restricciones",

            "mensaje":
                "El modelo de recomendación no encontró "
                "coincidencias exactas con los lugares "
                "aptos. Se entrega el Top 3 más seguro "
                "según restricciones.",

            "resultado_final": {

                "lugar_recomendado":
                    lugar_fallback,

                "top_3":
                    lugares_fallback
            },

            "datos_para_historial": {

                "apto":
                    bool(
                        lugares_fallback
                    ),

                "probabilidad_apto":
                    (
                        lugares_fallback[
                            0
                        ].get(
                            "probabilidad_apto"
                        )
                        if lugares_fallback
                        else None
                    ),

                "lugar_recomendado":
                    lugar_fallback,

                "ranking":
                    lugares_fallback
            }
        }


    # ========================================================
    # 6. RESULTADO FINAL
    # ========================================================

    lugar_recomendado = (
        ranking_final[
            0
        ][
            "lugar"
        ]
    )


    return {

        "estado":
            "recomendado",

        "mensaje":
            "Resultado final generado después de "
            "combinar restricciones, recomendación, "
            "distancia y datos reales de los lugares.",

        "modelo":
            "flujo_final_restricciones_y_recomendacion",

        "resultado_final": {

            "lugar_recomendado":
                lugar_recomendado,

            "top_3":
                ranking_final
        },

        "datos_para_historial": {

            "apto":
                True,

            "probabilidad_apto":
                ranking_final[
                    0
                ].get(
                    "probabilidad_apto_restricciones"
                ),

            "lugar_recomendado":
                lugar_recomendado,

            "ranking":
                ranking_final
        }
    }