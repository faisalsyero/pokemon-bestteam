from pydantic import BaseModel, Field


class HumanRating(BaseModel):
    game_id: str
    settings: dict
    entity_type: str = Field(pattern="^(pokemon|team)$")
    entity_ids: list[str]
    rating: float = Field(ge=0, le=100)
    rationale: list[str] = Field(default_factory=list)


class PairwisePreference(BaseModel):
    game_id: str
    team_a: list[str]
    team_b: list[str]
    preferred_team: str = Field(pattern="^(a|b)$")


def ranking_correlation(predicted: list[float], human: list[float]) -> float:
    """Return a simple Pearson correlation for calibration datasets."""
    if len(predicted) != len(human) or not predicted:
        return 0.0
    mean_a = sum(predicted) / len(predicted)
    mean_b = sum(human) / len(human)
    numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(predicted, human))
    denom_a = sum((a - mean_a) ** 2 for a in predicted)
    denom_b = sum((b - mean_b) ** 2 for b in human)
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return max(-1.0, min(1.0, numerator / (denom_a * denom_b) ** 0.5))
