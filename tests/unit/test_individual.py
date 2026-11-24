from pokemon_ai.data.loader import load_game
from pokemon_ai.mechanics.evolution import can_reach_evolution
from pokemon_ai.models import Evolution, EvolutionCondition, UserSettings
from pokemon_ai.scoring.individual import (
    availability_score,
    evolution_score,
    progression_contribution_score,
    score_pokemon,
)


def test_availability_missing_is_zero_and_trade_evolution_settings_work():
    pack = load_game("demo_game", "data")
    voltkit = next(item for item in pack["pokemon"] if item.id == "voltkit")
    settings = UserSettings(game_id="demo_game")
    trade = next(item for item in pack["evolutions"] if item.from_id == "voltkit")
    assert can_reach_evolution(trade, settings) is False
    patched = settings.model_copy(update={"trade_evolutions_patched": True})
    assert can_reach_evolution(trade, patched) is True
    score, reasons = evolution_score(voltkit, pack, settings)
    assert 0 <= score <= 100
    assert reasons


def test_unavailable_pokemon_progression_is_zero():
    pack = load_game("demo_game", "data")
    pokemon = pack["pokemon"][0].model_copy(update={"id": "not_in_game"})
    settings = UserSettings(game_id="demo_game")
    score, reasons = progression_contribution_score(pokemon, pack, settings)
    assert score == 0
    assert reasons


def test_score_pokemon_breakdown_is_clamped():
    pack = load_game("demo_game", "data")
    settings = UserSettings(game_id="demo_game")
    result = score_pokemon(pack["pokemon"][0], pack, settings)
    assert 0 <= result.total <= 100
    assert set(result.components) >= {
        "stats", "availability", "evolution", "movepool",
        "boss_performance", "progression", "reliability", "convenience",
    }
