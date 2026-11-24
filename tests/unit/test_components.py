from pokemon_ai.models import BaseStats, Pokemon
from pokemon_ai.scoring.components import clamp, stats_score


def make_pokemon(attack=50, special_attack=50, speed=50, hp=50, defense=50, special_defense=50):
    return Pokemon(
        id="test",
        species="Test",
        types=["normal"],
        base_stats=BaseStats(
            hp=hp,
            attack=attack,
            defense=defense,
            special_attack=special_attack,
            special_defense=special_defense,
            speed=speed,
        ),
        evolution_family="test",
    )


def test_clamp_limits_values():
    assert clamp(-1) == 0
    assert clamp(101) == 100
    assert clamp(42.5) == 42.5


def test_stats_score_physical_attacker():
    score, reasons = stats_score(make_pokemon(attack=150, special_attack=50))
    assert 0 <= score <= 100
    assert score > stats_score(make_pokemon(attack=50, special_attack=50))[0]
    assert reasons


def test_stats_score_special_attacker():
    score, _ = stats_score(make_pokemon(attack=50, special_attack=150))
    assert 0 <= score <= 100
