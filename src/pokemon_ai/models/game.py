from pydantic import BaseModel, Field


class Game(BaseModel):
    id: str
    title: str
    version: str
    generation: int = Field(ge=1)
    base_game: str | None = None
    difficulty_profiles: list[str] = Field(default_factory=lambda: ["normal"])
    source_notes: list[str] = Field(default_factory=list)
    data_completeness: float = Field(ge=0, le=1, default=1)
