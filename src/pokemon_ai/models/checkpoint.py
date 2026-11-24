from pydantic import BaseModel, Field


class Checkpoint(BaseModel):
    id: str
    name: str
    order: int = Field(ge=0)
    category: str
    level_cap: int | None = None
    newly_accessible_locations: list[str] = Field(default_factory=list)
    newly_available_items: list[str] = Field(default_factory=list)
    newly_available_moves: list[str] = Field(default_factory=list)
    newly_available_evolutions: list[str] = Field(default_factory=list)
    importance: float = Field(ge=0, le=1)
