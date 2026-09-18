"""Servicio de recomendaciones de actividades turísticas.

El objetivo de este servicio es recibir las respuestas del cuestionario de la
aplicación Flutter y generar recomendaciones personalizadas con base en un
conjunto curado de actividades disponibles en Villavicencio y sus alrededores.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, cast

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .ml_turismo.router import router as ml_router

app = FastAPI(
    title="Tourism Activity Recommendation Service",
    version="1.0.0",
    description=(
        "API independiente que procesa los cuestionarios de preferencias de "
        "App Turismo y devuelve sugerencias personalizadas basadas en reglas "
        "heurísticas."
    ),
)
app.include_router(
    ml_router
)

class SurveyPayload(BaseModel):
    """Estructura de las respuestas del cuestionario enviado por Flutter."""

    travel_style: str = Field(alias="travelStyle")
    interests: List[str]
    activity_level: str = Field(alias="activityLevel")
    travel_companions: str = Field(alias="travelCompanions")
    budget_level: str = Field(alias="budgetLevel")
    preferred_time_of_day: str = Field(alias="preferredTimeOfDay")
    additional_notes: str | None = Field(default=None, alias="additionalNotes")

    model_config = ConfigDict(populate_by_name=True)


class AvailableActivity(BaseModel):
    """Actividad disponible asociada a una ruta turística."""

    name: str
    route_name: str = Field(alias="routeName")
    route_description: str = Field(alias="routeDescription")
    route_difficulty: str = Field(alias="routeDifficulty")
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class RecommendationRequest(BaseModel):
    """Petición para generar recomendaciones de actividades."""

    user_id: str
    survey: SurveyPayload
    available_activities: List[AvailableActivity] = Field(
        default_factory=list, alias="availableActivities"
    )

    model_config = ConfigDict(populate_by_name=True)


class RecommendationOut(BaseModel):
    """Actividad sugerida."""

    activity_name: str = Field(alias="activityName")
    summary: str
    location: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendationOut]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="generatedAt")

    model_config = ConfigDict(populate_by_name=True)


class _ActivityTemplate(BaseModel):
    """Plantilla interna para evaluar coincidencias."""

    name: str
    summary: str
    location: str
    tags: List[str]
    travel_styles: List[str]
    activity_levels: List[str]
    companions: List[str]
    budgets: List[str]
    times_of_day: List[str]


class _RecommendationEngine:
    def __init__(self) -> None:
        self._profiles: Dict[str, Dict[str, object]] = {
            "miradores": {
                "summary": (
                    "Recorrido por los miradores de {route_name} para admirar los Llanos "
                    "Orientales y capturar fotografías panorámicas."
                ),
                "location": "{route_name} - Miradores",
                "tags": ["naturaleza", "panorama", "fotografia"],
                "travel_styles": ["relajado", "equilibrado"],
                "activity_levels": ["baja", "media"],
                "companions": ["familia", "pareja", "amigos", "solo"],
                "budgets": ["economico", "moderado"],
                "times_of_day": ["manana", "tarde"],
            },
            "parapente": {
                "summary": (
                    "Vuelo en parapente sobre {route_name} con instructores certificados "
                    "y vistas amplias de Villavicencio."
                ),
                "location": "Zona de parapente en {route_name}",
                "tags": ["aventura", "adrenalina", "naturaleza"],
                "travel_styles": ["aventurero", "equilibrado"],
                "activity_levels": ["media", "alta"],
                "companions": ["amigos", "pareja"],
                "budgets": ["moderado", "premium"],
                "times_of_day": ["manana", "tarde"],
            },
            "caminata ecológica": {
                "summary": (
                    "Sendero interpretativo por {route_name} para conocer la flora, la fauna "
                    "y las historias locales."
                ),
                "location": "{route_name}",
                "tags": ["naturaleza", "bienestar", "cultura"],
                "travel_styles": ["equilibrado", "relajado"],
                "activity_levels": ["media"],
                "companions": ["familia", "amigos", "pareja", "solo"],
                "budgets": ["economico", "moderado"],
                "times_of_day": ["manana", "tarde"],
            },
        }

    def recommend(
        self,
        survey: SurveyPayload,
        available_activities: List[AvailableActivity],
        limit: int = 5,
    ) -> List[RecommendationOut]:
        templates: List[_ActivityTemplate] = []
        for activity in available_activities:
            template = self._build_template(activity)
            if template is not None:
                templates.append(template)

        if not templates:
            return []

        scored = [
            (self._score_activity(activity, survey), activity)
            for activity in templates
        ]
        scored.sort(key=lambda item: item[0], reverse=True)

        recommendations: List[RecommendationOut] = []
        for score, activity in scored[: min(limit, len(scored))]:
            confidence = min(1.0, 0.25 + score / 10)
            recommendations.append(
                RecommendationOut(
                    activity_name=activity.name,
                    summary=activity.summary,
                    location=activity.location,
                    confidence=round(confidence, 2),
                    tags=activity.tags,
                    created_at=datetime.now(timezone.utc),
                )
            )
        return recommendations

    def _build_template(
        self, available: AvailableActivity
    ) -> _ActivityTemplate | None:
        key = available.name.strip().casefold()
        profile = self._profiles.get(key)
        if profile is not None:
            summary_template = cast(str, profile["summary"])
            location_template = cast(str, profile.get("location", "{route_name}"))
            tags = list(cast(List[str], profile["tags"]))
            extra_tags = [tag for tag in available.tags if tag not in tags]
            tags.extend(extra_tags)

            return _ActivityTemplate(
                name=available.name,
                summary=summary_template.format(
                    route_name=available.route_name,
                    route_description=available.route_description,
                    activity_name=available.name,
                ),
                location=location_template.format(
                    route_name=available.route_name,
                    activity_name=available.name,
                ),
                tags=tags,
                travel_styles=list(cast(List[str], profile["travel_styles"])),
                activity_levels=list(cast(List[str], profile["activity_levels"])),
                companions=list(cast(List[str], profile["companions"])),
                budgets=list(cast(List[str], profile["budgets"])),
                times_of_day=list(cast(List[str], profile["times_of_day"])),
            )

        return self._build_generic_template(available)

    def _build_generic_template(self, available: AvailableActivity) -> _ActivityTemplate:
        description = f"{available.route_description} {available.name}".lower()
        tags = set(available.tags)

        if "parapente" in description or "avent" in description:
            tags.update({"aventura", "naturaleza"})
        if "mirador" in description or "vista" in description:
            tags.update({"naturaleza", "panorama", "fotografia"})
        if "caminata" in description or "sender" in description:
            tags.update({"naturaleza", "bienestar"})
        if "relaj" in description or "bienestar" in description:
            tags.update({"bienestar", "relajacion"})
        if "cultura" in description or "hist" in description:
            tags.add("cultura")
        if not tags:
            tags.add("naturaleza")

        difficulty = available.route_difficulty.lower()
        if "alta" in difficulty:
            activity_levels = ["alta"]
        elif "media" in difficulty or "moder" in difficulty:
            activity_levels = ["media"]
        else:
            activity_levels = ["baja", "media"]

        travel_styles = ["equilibrado"]
        if "relaj" in description or "bienestar" in description:
            travel_styles.append("relajado")
        if "avent" in description or "parapente" in description or "alta" in difficulty:
            travel_styles.append("aventurero")

        companions = ["familia", "pareja", "amigos", "solo"]
        budgets = ["economico", "moderado"]
        if "premium" in description or "lujo" in description:
            budgets.append("premium")

        times_of_day = ["manana", "tarde"]
        if "noche" in description or "atardecer" in description or "noct" in description:
            times_of_day.append("noche")

        summary = (
            f"{available.name} en {available.route_name}. "
            f"{available.route_description.strip()}"
        ).strip()

        travel_styles = list(dict.fromkeys(travel_styles))
        budgets = list(dict.fromkeys(budgets))
        times_of_day = list(dict.fromkeys(times_of_day))

        return _ActivityTemplate(
            name=available.name,
            summary=summary,
            location=available.route_name,
            tags=sorted(tags),
            travel_styles=travel_styles,
            activity_levels=activity_levels,
            companions=companions,
            budgets=budgets,
            times_of_day=times_of_day,
        )

    def _score_activity(self, activity: _ActivityTemplate, survey: SurveyPayload) -> float:
        score = 0.0
        interests = set(survey.interests)
        score += 1.5 * len(interests.intersection(activity.tags))

        if survey.travel_style in activity.travel_styles:
            score += 1.2
        if survey.activity_level in activity.activity_levels:
            score += 1.0
        if survey.travel_companions in activity.companions:
            score += 0.8
        if survey.budget_level in activity.budgets:
            score += 0.6
        if survey.preferred_time_of_day in activity.times_of_day:
            score += 0.4

        if survey.additional_notes:
            lowered = survey.additional_notes.lower()
            keywords = {
                "veg": 0.3,
                "fot": 0.3,
                "niñ": 0.4,
                "adult": 0.2,
                "avent": 0.4,
            }
            for token, boost in keywords.items():
                if token in lowered:
                    score += boost
                    break

        return score


def _get_engine() -> _RecommendationEngine:
    # En un despliegue real se utilizaría inyección de dependencias o un
    # singleton thread-safe. Para este ejemplo sencillo basta con instanciarlo
    # una sola vez y reutilizarlo.
    if not hasattr(_get_engine, "_instance"):
        setattr(_get_engine, "_instance", _RecommendationEngine())
    return getattr(_get_engine, "_instance")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/recommendations", response_model=RecommendationResponse)
def create_recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    if not payload.survey.interests:
        raise HTTPException(status_code=400, detail="Debe indicar al menos un interés")
    if not payload.available_activities:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar las actividades disponibles para el usuario",
        )

    engine = _get_engine()
    recommendations = engine.recommend(
        payload.survey, payload.available_activities
    )

    if not recommendations:
        raise HTTPException(status_code=500, detail="No se pudieron generar recomendaciones")

    return RecommendationResponse(user_id=payload.user_id, recommendations=recommendations)
