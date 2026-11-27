from pokemon_ai.data.loader import load_game
from pokemon_ai.models import UserSettings
from pokemon_ai.optimisation.search import ExhaustiveOptimiser


def test_exhaustive_search_finds_a_team_on_tiny_pool():
    pack = load_game("demo_game", "data")
    settings = UserSettings(game_id="demo_game", team_size=3)
    result = ExhaustiveOptimiser().optimise(pack, settings)
    assert len(result.best_team) == 3
    assert len(set(result.best_team)) == 3
    assert result.candidates_evaluated > 0
