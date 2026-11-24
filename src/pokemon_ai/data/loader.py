import json
from pathlib import Path

from pokemon_ai.models import (
    Boss, Checkpoint, Encounter, Evolution, Game, Move,
    MoveAccess, Pokemon,
)


def _read_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in {path}: {exc}") from exc
    except FileNotFoundError as exc:
        raise ValueError(f"Missing required data file: {path}") from exc


def load_game(game_id: str, data_root: str | Path = "data") -> dict:
    """Load and validate a complete game data pack."""
    root = Path(data_root) / "games" / game_id
    if not root.is_dir():
        raise ValueError(f"Unknown game '{game_id}'. Expected data pack at {root}")

    game_data = _read_json(root / "game.json")
    game = Game.model_validate(game_data)
    pokemon = [Pokemon.model_validate(item) for item in _read_json(root / "pokemon.json")]
    moves = [Move.model_validate(item) for item in _read_json(root / "moves.json")]
    encounters = [Encounter.model_validate(item) for item in _read_json(root / "encounters.json")]
    evolutions = [Evolution.model_validate(item) for item in _read_json(root / "evolutions.json")]
    checkpoints = [Checkpoint.model_validate(item) for item in _read_json(root / "checkpoints.json")]
    bosses = [Boss.model_validate(item) for item in _read_json(root / "bosses.json")]

    move_access_data = _read_json(root / "move_access.json") if (root / "move_access.json").exists() else []
    move_access = [MoveAccess.model_validate(item) for item in move_access_data]
    pokemon_by_id = {item.id: item for item in pokemon}
    move_by_id = {item.id: item for item in moves}
    for encounter in encounters:
        if encounter.pokemon_id not in pokemon_by_id:
            raise ValueError(f"Encounter references unknown Pokémon '{encounter.pokemon_id}'")
    for evolution in evolutions:
        if evolution.from_id not in pokemon_by_id or evolution.to_id not in pokemon_by_id:
            raise ValueError(f"Evolution references unknown Pokémon: {evolution.from_id} -> {evolution.to_id}")
    for access in move_access:
        if access.pokemon_id not in pokemon_by_id or access.move_id not in move_by_id:
            raise ValueError(f"Move access references unknown Pokémon or move: {access}")

    return {
        "game": game,
        "pokemon": pokemon,
        "moves": moves,
        "move_access": move_access,
        "encounters": encounters,
        "evolutions": evolutions,
        "checkpoints": sorted(checkpoints, key=lambda item: item.order),
        "bosses": sorted(bosses, key=lambda item: next(cp.order for cp in checkpoints if cp.id == item.checkpoint_id)),
        "type_chart": (root / "type_chart.json").as_posix(),
    }
