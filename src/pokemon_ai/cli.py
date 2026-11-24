from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pokemon_ai.data.loader import load_game
from pokemon_ai.data.validator import validate_game
from pokemon_ai.scoring.individual import score_pokemon
from pokemon_ai.models import UserSettings

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
