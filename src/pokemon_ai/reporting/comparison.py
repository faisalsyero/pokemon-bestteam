from pokemon_ai.optimisation.base import OptimisationResult


def compare_results(results: list[OptimisationResult]) -> list[dict]:
    return [
        {
            "algorithm": result.algorithm,
            "team": result.best_team,
            "score": result.score_breakdown.total,
            "runtime_seconds": round(result.runtime_seconds, 4),
            "candidates_evaluated": result.candidates_evaluated,
            "optimality_proven": result.optimality_proven,
        }
        for result in sorted(results, key=lambda item: item.score_breakdown.total, reverse=True)
    ]
