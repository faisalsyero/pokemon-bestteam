import itertools
import random
import time
from pathlib import Path

from pokemon_ai.models import Team, UserSettings
from pokemon_ai.optimisation.base import OptimisationResult, Optimiser
from pokemon_ai.scoring.team import score_team


def candidate_pool(game: dict, settings: UserSettings) -> list[str]:
    pool: list[str] = []
    by_id = {pokemon.id: pokemon for pokemon in game["pokemon"]}
    for pokemon_id, pokemon in by_id.items():
        if pokemon_id in settings.banned_pokemon:
            continue
        if "legendary" in pokemon.tags and not settings.legendaries_allowed:
            continue
        if "mythical" in pokemon.tags and not settings.mythicals_allowed:
            continue
        if pokemon_id not in settings.core_pokemon:
            pool.append(pokemon_id)
    return sorted(set(pool))


def _team_result(game: dict, settings: UserSettings, team_ids: list[str], algorithm: str, seed: int, started: float, evaluated: int, reason: str, optimal: bool = False) -> OptimisationResult:
    team = Team(pokemon_ids=team_ids)
    breakdown = score_team(team, game, settings)
    return OptimisationResult(
        best_team=team_ids,
        score_breakdown=breakdown,
        algorithm=algorithm,
        seed=seed,
        runtime_seconds=time.perf_counter() - started,
        candidates_evaluated=evaluated,
        stopping_reason=reason,
        optimality_proven=optimal,
    )


class ExhaustiveOptimiser(Optimiser):
    def optimise(self, game: dict, settings: UserSettings) -> OptimisationResult:
        started = time.perf_counter()
        pool = candidate_pool(game, settings)
        core = list(dict.fromkeys(settings.core_pokemon))
        size = settings.team_size
        best_ids: list[str] = core[:size]
        best_score = -1.0
        evaluated = 0
        alternatives: list[list[str]] = []
        for additions in itertools.combinations(pool, max(0, size - len(core))):
            ids = sorted(set(core + list(additions)))
            if len(ids) != size:
                continue
            result = score_team(Team(pokemon_ids=ids), game, settings)
            evaluated += 1
            if result.total > best_score:
                best_score = result.total
                best_ids = ids
            alternatives.append(ids)
        result = _team_result(game, settings, best_ids, "exhaustive", settings.random_seed, started, evaluated, "All legal combinations considered", True)
        result.alternative_teams = sorted(alternatives, key=lambda ids: score_team(Team(pokemon_ids=ids), game, settings).total, reverse=True)[:5]
        return result


class RandomOptimiser(Optimiser):
    def optimise(self, game: dict, settings: UserSettings) -> OptimisationResult:
        started = time.perf_counter()
        rng = random.Random(settings.random_seed)
        pool = candidate_pool(game, settings)
        core = list(dict.fromkeys(settings.core_pokemon))
        evaluated = 0
        best_ids = sorted(core)
        best_score = -1.0
        alternatives: dict[tuple[str, ...], float] = {}
        budget = max(20, min(2000, int(settings.runtime_seconds * 100)))
        for _ in range(budget):
            needed = settings.team_size - len(core)
            if needed < 0:
                break
            ids = sorted(set(core + rng.sample(pool, k=min(needed, len(pool)))))
            if len(ids) < 1:
                continue
            if len(ids) > settings.team_size:
                continue
            evaluated += 1
            score = score_team(Team(pokemon_ids=ids), game, settings)
            alternatives[tuple(ids)] = score.total
            if score.total > best_score:
                best_score = score.total
                best_ids = ids
        result = _team_result(game, settings, best_ids, "random", settings.random_seed, started, evaluated, "Search budget exhausted")
        result.alternative_teams = [list(ids) for ids, _ in sorted(alternatives.items(), key=lambda item: (-item[1], item[0]))[:5]]
        return result


class GreedyOptimiser(Optimiser):
    def optimise(self, game: dict, settings: UserSettings) -> OptimisationResult:
        started = time.perf_counter()
        pool = candidate_pool(game, settings)
        ids = list(dict.fromkeys(settings.core_pokemon))
        evaluated = 0
        while len(ids) < settings.team_size:
            best_ids: list[str] | None = None
            best_score = -1.0
            for candidate in pool:
                if candidate in ids:
                    continue
                trial = sorted(ids + [candidate])
                evaluated += 1
                score = score_team(Team(pokemon_ids=trial), game, settings)
                if score.total > best_score:
                    best_score = score.total
                    best_ids = trial
            if best_ids is None:
                break
            ids = best_ids
        return _team_result(game, settings, ids, "greedy", settings.random_seed, started, evaluated, "No candidate improved the partial team")


class BeamSearchOptimiser(Optimiser):
    def __init__(self, beam_width: int = 20) -> None:
        self.beam_width = beam_width

    def optimise(self, game: dict, settings: UserSettings) -> OptimisationResult:
        started = time.perf_counter()
        pool = candidate_pool(game, settings)
        core = list(dict.fromkeys(settings.core_pokemon))
        beam: list[list[str]] = [sorted(core)]
        seen = {tuple(sorted(core))}
        evaluated = 0
        while len(beam[0]) < settings.team_size:
            expanded: dict[tuple[str, ...], float] = {}
            for ids in beam:
                for candidate in pool:
                    if candidate in ids:
                        continue
                    trial = sorted(ids + [candidate])
                    signature = tuple(trial)
                    if signature in seen:
                        continue
                    seen.add(signature)
                    evaluated += 1
                    score = score_team(Team(pokemon_ids=trial), game, settings)
                    expanded[signature] = score.total
            if not expanded:
                break
            beam = [list(ids) for ids, _ in sorted(expanded.items(), key=lambda item: (-item[1], item[0]))[:self.beam_width]]
        finals = [(ids, score_team(Team(pokemon_ids=ids), game, settings).total) for ids in beam]
        best_ids, _ = max(finals, key=lambda item: (item[1], tuple(reversed(item[0]))))
        result = _team_result(game, settings, best_ids, "beam", settings.random_seed, started, evaluated, "Beam width exhausted")
        result.alternative_teams = [ids for ids, _ in sorted(finals, key=lambda item: (-item[1], item[0]))[:5]]
        return result
