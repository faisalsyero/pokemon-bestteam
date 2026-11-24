from pokemon_ai.models import Pokemon, UserSettings


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def stats_score(pokemon: Pokemon) -> tuple[float, list[str]]:
    stats = pokemon.base_stats
    max_attack = max(stats.attack, stats.special_attack)
    offence = clamp((max_attack - 35) / 95 * 100)
    speed = clamp((stats.speed - 35) / 95 * 100)
    physical_bulk = clamp((stats.hp + stats.defense - 100) / 150 * 100)
    special_bulk = clamp((stats.hp + stats.special_defense - 100) / 150 * 100)
    hp = clamp((stats.hp - 20) / 100 * 100)
    role_balance = clamp(100 - abs(stats.attack - stats.special_attack) / 1.5)
    score = clamp(offence * 0.40 + speed * 0.20 + physical_bulk * 0.15 + special_bulk * 0.15 + hp * 0.10)
    # Role balance is informational here so mixed attackers do not receive a harsh penalty.
    reasons = [f"Best offence {max_attack}, speed {stats.speed}, balanced attacking stats {role_balance:.1f}"]
    return score, reasons
