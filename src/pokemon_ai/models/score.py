from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    total: float = Field(ge=0, le=100)
    components: dict[str, float] = Field(default_factory=dict)
    bonuses: dict[str, float] = Field(default_factory=dict)
    penalties: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
