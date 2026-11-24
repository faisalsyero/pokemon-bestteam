from pokemon_ai.data.loader import load_game
from pokemon_ai.data.validator import validate_game
from pokemon_ai.models import UserSettings
from pokemon_ai.scoring.individual import score_pokemon


def test_complete_demo_game_loads_and_scores():
    pack = load_game("demo_game", "data")
    assert len(pack["pokemon"]) >= 10
    assert len(pack["bosses"]) >= 4
    settings = UserSettings(game_id="demo_game")
    scores = [score_pokemon(pokemon, pack, settings) for pokemon in pack["pokemon"]]
    assert all(0 <= score.total <= 100 for score in scores)
    assert all(score.reasons for score in scores)


def test_validate_demo_game_summary():
    summary = validate_game("demo_game", "data")
    assert any("Pokémon:" in line for line in summary)
    assert any("Bosses:" in line for line in summary)
