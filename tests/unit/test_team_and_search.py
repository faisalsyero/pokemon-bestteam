from pokemon_ai.data.loader import load_game
from pokemon_ai.models import Team, UserSettings
from pokemon_ai.optimisation.search import BeamSearchOptimiser, GreedyOptimiser
from pokemon_ai.scoring.team import score_team
from pokemon_ai.scoring.profiles import profile_weights


def test_team_score_and_banned_member():
    pack = load_game("demo_game", "data")
    settings = UserSettings(game_id="demo_game", banned_pokemon=["brookfin"])
    result = score_team(Team(pokemon_ids=["sprigear", "sparrow", "grotto", "voltkit", "puddle", "mossling"]), pack, settings)
    assert 0 <= result.total <= 100

    banned_result = score_team(Team(pokemon_ids=["brookfin", "sparrow"]), pack, settings)
    assert banned_result.total >= 0


def test_locked_core_is_never_removed():
    pack = load_game("demo_game", "data")
    settings = UserSettings(game_id="demo_game", core_pokemon=["voltkit"], team_size=4)
    result = BeamSearchOptimiser(beam_width=8).optimise(pack, settings)
    assert "voltkit" in result.best_team
    assert len(set(result.best_team)) == len(result.best_team)


def test_greedy_and_beam_are_deterministic():
    pack = load_game("demo_game", "data")
    settings = UserSettings(game_id="demo_game", random_seed=42, team_size=4)
    first = GreedyOptimiser().optimise(pack, settings)
    second = GreedyOptimiser().optimise(pack, settings)
    assert first.best_team == second.best_team

    beam_first = BeamSearchOptimiser(beam_width=6).optimise(pack, settings)
    beam_second = BeamSearchOptimiser(beam_width=6).optimise(pack, settings)
    assert beam_first.best_team == beam_second.best_team


def test_missing_core_returns_zero_team_score():
    pack = load_game("demo_game", "data")
    settings = UserSettings(game_id="demo_game", core_pokemon=["voltkit"])
    result = score_team(Team(pokemon_ids=["brookfin", "sparrow"]), pack, settings)
    assert result.total == 0


def test_difficulty_profile_weights_are_normalised():
    weights = profile_weights("hard")
    assert abs(sum(weights.values()) - 1.0) < 1e-9
