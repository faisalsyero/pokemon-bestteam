from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pokemon_ai.data.loader import load_game
from pokemon_ai.data.validator import validate_game
from pokemon_ai.scoring.individual import score_pokemon
from pokemon_ai.models import UserSettings
from pokemon_ai.models import Team
from pokemon_ai.scoring.team import score_team
from pokemon_ai.optimisation.search import BeamSearchOptimiser, ExhaustiveOptimiser, GreedyOptimiser, RandomOptimiser
from pokemon_ai.optimisation.advanced import GeneticOptimiser, SimulatedAnnealingOptimiser, TabuOptimiser, HybridOptimiser
from pokemon_ai.planning.roster import build_roster_plan
from pokemon_ai.reporting.comparison import compare_results

app = typer.Typer(help="Rank Pokémon for a complete playthrough.")
console = Console()
DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def _load(game: str) -> dict:
    try:
        return load_game(game, DATA_ROOT)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command("validate-data")
def validate_data(game: str = typer.Option(..., "--game")) -> None:
    """Validate a game data pack."""
    try:
        lines = validate_game(game, DATA_ROOT)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print("\n".join(lines), style="green")


@app.command("rank-pokemon")
def rank_pokemon(game: str = typer.Option(..., "--game")) -> None:
    """Rank all allowed Pokémon in a game pack."""
    pack = _load(game)
    settings = UserSettings(game_id=game)
    rows = []
    for pokemon in pack["pokemon"]:
        score = score_pokemon(pokemon, pack, settings)
        rows.append((pokemon.id, score.total))
    table = Table(title=f"Rankings — {pack['game'].title}")
    table.add_column("Pokémon")
    table.add_column("Score", justify="right")
    for pokemon_id, score in sorted(rows, key=lambda row: (-row[1], row[0])):
        table.add_row(pokemon_id, f"{score:.1f}")
    console.print(table)


@app.command("score-pokemon")
def score_pokemon_command(
    game: str = typer.Option(..., "--game"),
    pokemon: str = typer.Option(..., "--pokemon"),
) -> None:
    """Show the explainable score breakdown for one Pokémon."""
    pack = _load(game)
    match = next((item for item in pack["pokemon"] if item.id == pokemon), None)
    if match is None:
        raise typer.BadParameter(f"Unknown Pokémon '{pokemon}'")
    result = score_pokemon(match, pack, UserSettings(game_id=game))
    console.print(f"[bold]{match.species}: {result.total:.1f}[/bold]")
    for name, value in result.components.items():
        console.print(f"  {name.replace('_', ' ').title():24s} {value:.1f}")
    for reason in result.reasons:
        console.print(f"  - {reason}")
    console.print(f"  Confidence: {result.confidence:.0%}")


@app.command("score-team")
def score_team_command(
    game: str = typer.Option(..., "--game"),
    team: str = typer.Option(..., "--team"),
) -> None:
    pack = _load(game)
    ids = [item.strip() for item in team.split(",") if item.strip()]
    unknown = [item for item in ids if item not in {pokemon.id for pokemon in pack["pokemon"]}]
    if unknown:
        raise typer.BadParameter(f"Unknown Pokémon: {', '.join(unknown)}")
    result = score_team(Team(pokemon_ids=ids), pack, UserSettings(game_id=game))
    console.print(f"[bold]Team score: {result.total:.1f}[/bold]")
    for name, value in result.components.items():
        console.print(f"  {name.replace('_', ' ').title():28s} {value:.1f}")
    for reason in result.reasons:
        console.print(f"  - {reason}")


@app.command("optimise")
def optimise_command(
    game: str = typer.Option(..., "--game"),
    algorithm: str = typer.Option("beam", "--algorithm"),
    core: str | None = typer.Option(None, "--core"),
    trades: bool = typer.Option(False, "--trades"),
    team_size: int = typer.Option(6, "--team-size"),
    seed: int = typer.Option(42, "--seed"),
) -> None:
    pack = _load(game)
    core_ids = [item.strip() for item in core.split(",")] if core else []
    unknown = [item for item in core_ids if item not in {pokemon.id for pokemon in pack["pokemon"]}]
    if unknown:
        raise typer.BadParameter(f"Unknown core Pokémon: {', '.join(unknown)}")
    settings = UserSettings(
        game_id=game,
        core_pokemon=core_ids,
        trades_allowed=trades,
        external_trading_allowed=trades,
        team_size=team_size,
        random_seed=seed,
    )
    optimisers = {
        "exhaustive": ExhaustiveOptimiser(),
        "random": RandomOptimiser(),
        "greedy": GreedyOptimiser(),
        "beam": BeamSearchOptimiser(),
        "genetic": GeneticOptimiser(),
        "simulated_annealing": SimulatedAnnealingOptimiser(),
        "tabu": TabuOptimiser(),
        "hybrid": HybridOptimiser(),
    }
    if algorithm not in optimisers:
        raise typer.BadParameter(f"Unknown algorithm '{algorithm}'. Choose: {', '.join(optimisers)}")
    result = optimisers[algorithm].optimise(pack, settings)
    console.print(f"[bold]Best team: {', '.join(result.best_team)}[/bold]")
    console.print(f"Score: {result.score_breakdown.total:.1f}")
    console.print(f"Algorithm: {result.algorithm} (heuristic: {not result.optimality_proven})")
    console.print(f"Candidates evaluated: {result.candidates_evaluated}")
    for reason in result.score_breakdown.reasons:
        console.print(f"  - {reason}")
    if result.alternative_teams:
        console.print("[bold]Alternatives[/bold]")
        for ids in result.alternative_teams[:5]:
            console.print("  " + ", ".join(ids))


@app.command("compare-algorithms")
def compare_algorithms_command(
    game: str = typer.Option(..., "--game"),
    seed: int = typer.Option(42, "--seed"),
) -> None:
    pack = _load(game)
    settings = UserSettings(game_id=game, random_seed=seed)
    optimisers = [
        GreedyOptimiser(),
        BeamSearchOptimiser(),
        RandomOptimiser(),
        GeneticOptimiser(population_size=20, generations=10),
    ]
    results = [optimiser.optimise(pack, settings) for optimiser in optimisers]
    table = Table(title="Optimiser comparison")
    table.add_column("Algorithm")
    table.add_column("Score", justify="right")
    table.add_column("Candidates", justify="right")
    for row in compare_results(results):
        table.add_row(row["algorithm"], f"{row['score']:.1f}", str(row["candidates_evaluated"]))
    console.print(table)


@app.command("progression-plan")
def progression_plan_command(
    game: str = typer.Option(..., "--game"),
    team: str = typer.Option(..., "--team"),
) -> None:
    pack = _load(game)
    ids = [item.strip() for item in team.split(",") if item.strip()]
    plan = build_roster_plan(Team(pokemon_ids=ids), pack, UserSettings(game_id=game))
    table = Table(title="Progression plan")
    table.add_column("Checkpoint")
    table.add_column("Available")
    table.add_column("Temporary member?")
    for stage in plan:
        names = ", ".join(item["pokemon_id"] for item in stage["available_team_members"]) or "None yet"
        table.add_row(stage["name"], names, "Yes" if stage["temporary_member_needed"] else "No")
    console.print(table)
