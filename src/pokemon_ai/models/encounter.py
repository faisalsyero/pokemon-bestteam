from pydantic import BaseModel, Field


class Encounter(BaseModel):
    pokemon_id: str
    location: str
    first_checkpoint: str
    method: str = "grass"
    encounter_rate: float = Field(ge=0, le=1)
    level_range: list[int] = Field(min_length=1, max_length=2)
    version_restriction: str | None = None
    required_field_move: str | None = None
    required_item: str | None = None
    detour_cost: float = Field(ge=0, le=100, default=0)
    probability_reliability: float = Field(ge=0, le=1, default=1)
