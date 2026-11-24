import json
from pathlib import Path


def load_type_chart(path: str | Path) -> dict[str, dict[str, float]]:
    """Load a generation-specific attacker/defender type effectiveness chart."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    chart = data.get("chart", data)
    return {attack.lower(): {defense.lower(): float(value) for defense, value in row.items()} for attack, row in chart.items()}


def effectiveness(chart: dict[str, dict[str, float]], attack_type: str, defender_types: list[str]) -> float:
    """Return combined type effectiveness, clamped to 0.25–4.0 for playthrough scoring."""
    result = 1.0
    for defense in defender_types:
        result *= chart.get(attack_type.lower(), {}).get(defense.lower(), 1.0)
    return max(0.25, min(4.0, result))
