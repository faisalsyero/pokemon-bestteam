from pokemon_ai.config import INDIVIDUAL_WEIGHTS


def get_individual_weights(overrides: dict[str, float] | None = None) -> dict[str, float]:
    """Validate and return individual score weights."""
    weights = dict(INDIVIDUAL_WEIGHTS)
    if overrides:
        weights.update(overrides)
    applicable = {key: max(0.0, float(value)) for key, value in weights.items()}
    total = sum(applicable.values())
    if total <= 0:
        raise ValueError("Individual weights must sum to more than zero")
    return {key: value / total for key, value in applicable.items()}
