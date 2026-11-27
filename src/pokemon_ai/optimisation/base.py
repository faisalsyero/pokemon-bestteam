from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from pokemon_ai.models import ScoreBreakdown


class OptimisationResult(BaseModel):
    best_team: list[str]
    score_breakdown: ScoreBreakdown
    alternative_teams: list[list[str]] = Field(default_factory=list)
    algorithm: str
    seed: int
    runtime_seconds: float
    candidates_evaluated: int
    stopping_reason: str
    optimality_proven: bool = False


class Optimiser(ABC):
    @abstractmethod
    def optimise(self, game: dict, settings) -> OptimisationResult:
        """Find a strong legal team using this optimiser."""
