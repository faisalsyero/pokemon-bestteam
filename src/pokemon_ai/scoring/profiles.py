DIFFICULTY_PROFILES: dict[str, dict[str, float]] = {
    "casual": {"progression": 0.35, "reliability": 0.10, "convenience": 0.15},
    "normal": {"progression": 0.40, "boss_performance": 0.20, "movepool": 0.10},
    "hard": {"progression": 0.35, "boss_performance": 0.25, "stats": 0.15},
    "hardcore": {"boss_performance": 0.30, "reliability": 0.15, "evolution": 0.10},
    "minimal_grinding": {"convenience": 0.20, "availability": 0.15, "progression": 0.35},
    "speed-oriented": {"boss_performance": 0.25, "stats": 0.20, "progression": 0.30},
    "safest": {"reliability": 0.20, "evolution": 0.10, "availability": 0.15},
    "offensive": {"stats": 0.25, "boss_performance": 0.25, "movepool": 0.15},
    "core-abuse": {"boss_performance": 0.30, "progression": 0.30, "stats": 0.15},
}


def profile_weights(profile: str) -> dict[str, float]:
    """Return profile overrides and keep unspecified values at normal defaults."""
    if not profile.strip():
        raise ValueError("Difficulty profile cannot be empty")
    if profile not in DIFFICULTY_PROFILES:
        raise ValueError(f"Unknown difficulty profile '{profile}'")
    base = {
        "progression": 0.40,
        "boss_performance": 0.20,
        "movepool": 0.10,
        "stats": 0.10,
        "evolution": 0.05,
        "availability": 0.05,
        "reliability": 0.05,
        "convenience": 0.05,
    }
    base.update(DIFFICULTY_PROFILES[profile])
    total = sum(base.values())
    return {key: value / total for key, value in base.items()}
