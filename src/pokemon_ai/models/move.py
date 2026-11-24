from pydantic import BaseModel, Field


class Move(BaseModel):
    id: str
    name: str
    type: str
    category: str
    base_power: int = Field(ge=0, default=0)
    accuracy: int | None = Field(ge=1, le=100, default=None)
    priority: int = 0
    pp: int = Field(ge=1, default=10)
    target: str = "single"
    secondary_effect: dict = Field(default_factory=dict)
    stat_changes: dict[str, int] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class MoveAccess(BaseModel):
    pokemon_id: str
    move_id: str
    source: str
    checkpoint: str | None = None
    level: int | None = None
    reusable: bool = True
    pre_evolution_only: bool = False
