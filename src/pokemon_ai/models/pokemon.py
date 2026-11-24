from pydantic import BaseModel, Field, field_validator


class BaseStats(BaseModel):
    hp: int = Field(ge=1, le=255)
    attack: int = Field(ge=1, le=255)
    defense: int = Field(ge=1, le=255)
    special_attack: int = Field(ge=1, le=255)
    special_defense: int = Field(ge=1, le=255)
    speed: int = Field(ge=1, le=255)

    @property
    def total(self) -> int:
        return sum(self.model_dump().values())


class Pokemon(BaseModel):
    id: str
    species: str
    form: str = "default"
    types: list[str]
    base_stats: BaseStats
    abilities: list[str] = Field(default_factory=list)
    evolution_family: str
    growth_rate: str = "medium_fast"
    gender_restrictions: list[str] = Field(default_factory=list)
    held_item_requirements: list[str] = Field(default_factory=list)
    form_change_requirements: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    display_name: str | None = None

    @field_validator("types")
    @classmethod
    def validate_types(cls, value: list[str]) -> list[str]:
        if not 1 <= len(value) <= 2:
            raise ValueError("A Pokémon must have one or two types")
        return [item.lower() for item in value]
