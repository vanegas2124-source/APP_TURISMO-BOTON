from math import (
    radians,
    sin,
    cos,
    sqrt,
    atan2
)

from typing import Optional


def calcular_distancia_km(
    lat1: float,
    lon1: float,
    lat2: Optional[float],
    lon2: Optional[float]
) -> Optional[float]:

    if lat2 is None or lon2 is None:
        return None

    radio_tierra_km = 6371.0

    lat1_rad = radians(float(lat1))
    lon1_rad = radians(float(lon1))

    lat2_rad = radians(float(lat2))
    lon2_rad = radians(float(lon2))

    diferencia_lat = (
        lat2_rad - lat1_rad
    )

    diferencia_lon = (
        lon2_rad - lon1_rad
    )

    a = (
        sin(diferencia_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(diferencia_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return round(
        radio_tierra_km * c,
        2
    )