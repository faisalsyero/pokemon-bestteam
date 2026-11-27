from pokemon_ai.mechanics.type_chart import effectiveness


def estimate_damage(
    level: int,
    attack: int,
    defense: int,
    move_power: int,
    stab: bool,
    effectiveness_multiplier: float,
    critical: bool = False,
    spread: bool = False,
) -> dict[str, float | int]:
    """Return transparent heuristic damage features, not a battle simulator."""
    if move_power <= 0 or defense <= 0:
        return {"low_percent": 0.0, "high_percent": 0.0, "hits_to_ko": 99}
    level_factor = (2 * level / 5 + 2)
    base = ((level_factor * move_power * attack / defense) / 50 + 2)
    base *= 1.5 if stab else 1.0
    base *= effectiveness_multiplier
    base *= 0.75 if spread else 1.0
    low = base * 0.85 * (1.5 if critical else 1.0)
    high = base * 1.0 * (1.5 if critical else 1.0)
    hits_low = max(1, round(100 / max(low, 1)))
    return {
        "low_percent": round(low, 1),
        "high_percent": round(high, 1),
        "hits_to_ko": hits_low,
        "critical": critical,
    }
