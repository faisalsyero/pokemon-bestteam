import math
import random
import time

from pokemon_ai.models import Team
from pokemon_ai.optimisation.base import OptimisationResult, Optimiser
from pokemon_ai.optimisation.search import candidate_pool
from pokemon_ai.scoring.team import score_team


def legal_team(rng: random.Random, pool: list[str], core: list[str], size: int) -> list[str]:
    needed = max(0, size - len(set(core)))
    additions = rng.sample(pool, k=min(needed, len(pool)))
    return sorted(set(core + additions))[:size]


def team_score(game: dict, settings, ids: list[str]) -> float:
    return score_team(Team(pokemon_ids=ids), game, settings).total


class GeneticOptimiser(Optimiser):
    def __init__(self, population_size: int = 30, generations: int = 20) -> None:
        self.population_size = population_size
        self.generations = generations

    def optimise(self, game: dict, settings) -> OptimisationResult:
        started = time.perf_counter()
        rng = random.Random(settings.random_seed)
        pool = candidate_pool(game, settings)
        core = list(dict.fromkeys(settings.core_pokemon))
        population = {tuple(legal_team(rng, pool, core, settings.team_size)) for _ in range(self.population_size)}
        evaluated = len(population)
        best = max(population, key=lambda ids: team_score(game, settings, list(ids)))
        stagnation = 0
        for _ in range(self.generations):
            ranked = sorted(population, key=lambda ids: (-team_score(game, settings, list(ids)), ids))
            elites = ranked[:max(2, len(ranked) // 10)]
            children = set(elites)
            while len(children) < self.population_size:
                parent_a = rng.choice(ranked[:max(2, len(ranked) // 2)])
                parent_b = rng.choice(ranked[:max(2, len(ranked) // 2)])
                cut = rng.randrange(1, settings.team_size)
                mixed = list(dict.fromkeys(list(parent_a[:cut]) + list(parent_b[cut:])))
                if len(mixed) < settings.team_size:
                    for member in pool:
                        if member not in mixed and member not in core:
                            mixed.append(member)
                        if len(mixed) == settings.team_size:
                            break
                if rng.random() < 0.25:
                    mutable = [member for member in mixed if member not in core]
                    if mutable:
                        old = rng.choice(mutable)
                        new = rng.choice([member for member in pool if member not in mixed])
                        mixed = [new if member == old else member for member in mixed]
                child = sorted(set(core + [member for member in mixed if member not in core]))
                if len(child) == settings.team_size:
                    children.add(tuple(child))
            population = children
            evaluated += len(population)
            candidate = max(population, key=lambda ids: team_score(game, settings, list(ids)))
            if team_score(game, settings, list(candidate)) > team_score(game, settings, list(best)):
                best = candidate
                stagnation = 0
            else:
                stagnation += 1
            if stagnation >= 5:
                break
        breakdown = score_team(Team(pokemon_ids=list(best)), game, settings)
        alternatives = sorted(population, key=lambda ids: (-team_score(game, settings, list(ids)), ids))[:5]
        return OptimisationResult(
            best_team=list(best), score_breakdown=breakdown, alternative_teams=[list(ids) for ids in alternatives],
            algorithm="genetic", seed=settings.random_seed, runtime_seconds=time.perf_counter() - started,
            candidates_evaluated=evaluated, stopping_reason="Stagnation or generation limit reached",
        )


class SimulatedAnnealingOptimiser(Optimiser):
    def optimise(self, game: dict, settings) -> OptimisationResult:
        started = time.perf_counter()
        rng = random.Random(settings.random_seed)
        pool = candidate_pool(game, settings)
        core = list(dict.fromkeys(settings.core_pokemon))
        current = legal_team(rng, pool, core, settings.team_size)
        current_score = team_score(game, settings, current)
        best = list(current)
        best_score = current_score
        evaluated = 1
        iterations = max(100, min(3000, int(settings.runtime_seconds * 100)))
        for step in range(iterations):
            replaceable = [member for member in current if member not in core]
            if not replaceable:
                break
            old = rng.choice(replaceable)
            choices = [member for member in pool if member not in current]
            if not choices:
                break
            new = rng.choice(choices)
            candidate = sorted(new if member == old else member for member in current)
            candidate_score = team_score(game, settings, candidate)
            evaluated += 1
            temperature = max(0.5, 10 * (1 - step / iterations))
            delta = candidate_score - current_score
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current, current_score = candidate, candidate_score
            if candidate_score > best_score:
                best, best_score = list(candidate), candidate_score
        return OptimisationResult(
            best_team=best, score_breakdown=score_team(Team(pokemon_ids=best), game, settings),
            algorithm="simulated_annealing", seed=settings.random_seed,
            runtime_seconds=time.perf_counter() - started, candidates_evaluated=evaluated,
            stopping_reason="Cooling schedule completed",
        )


class TabuOptimiser(Optimiser):
    def optimise(self, game: dict, settings) -> OptimisationResult:
        started = time.perf_counter()
        rng = random.Random(settings.random_seed)
        pool = candidate_pool(game, settings)
        core = list(dict.fromkeys(settings.core_pokemon))
        current = legal_team(rng, pool, core, settings.team_size)
        best = list(current)
        tabu: dict[tuple[str, ...], int] = {}
        evaluated = 1
        for step in range(max(100, min(2000, int(settings.runtime_seconds * 100)))):
            choices: list[list[str]] = []
            replaceable = [member for member in current if member not in core]
            for old in replaceable:
                for new in pool:
                    if new not in current:
                        choices.append(sorted(new if member == old else member for member in current))
            choices = [ids for ids in choices if tuple(ids) not in tabu or tabu[tuple(ids)] <= step]
            if not choices:
                break
            candidate = max(choices, key=lambda ids: (team_score(game, settings, ids), tuple(reversed(ids))))
            evaluated += 1
            tabu[tuple(candidate)] = step + 5
            current = candidate
            if team_score(game, settings, candidate) > team_score(game, settings, best):
                best = list(candidate)
        return OptimisationResult(
            best_team=best, score_breakdown=score_team(Team(pokemon_ids=best), game, settings),
            algorithm="tabu", seed=settings.random_seed, runtime_seconds=time.perf_counter() - started,
            candidates_evaluated=evaluated, stopping_reason="Iteration budget exhausted",
        )


class HybridOptimiser(Optimiser):
    def optimise(self, game: dict, settings) -> OptimisationResult:
        from pokemon_ai.optimisation.search import BeamSearchOptimiser
        started = time.perf_counter()
        beam = BeamSearchOptimiser(beam_width=12).optimise(game, settings)
        genetic = GeneticOptimiser(population_size=20, generations=10).optimise(game, settings)
        candidates = [beam.best_team, genetic.best_team, *genetic.alternative_teams]
        best = max(candidates, key=lambda ids: team_score(game, settings, ids))
        tabu = TabuOptimiser().optimise(game, settings)
        if team_score(game, settings, tabu.best_team) > team_score(game, settings, best):
            best = tabu.best_team
        return OptimisationResult(
            best_team=best, score_breakdown=score_team(Team(pokemon_ids=best), game, settings),
            alternative_teams=candidates[:5], algorithm="hybrid", seed=settings.random_seed,
            runtime_seconds=time.perf_counter() - started,
            candidates_evaluated=beam.candidates_evaluated + genetic.candidates_evaluated + tabu.candidates_evaluated,
            stopping_reason="Beam, genetic, and tabu finalists evaluated",
        )
