from pokemon_ai.data.loader import load_game


def validate_game(game_id: str, data_root: str = "data") -> list[str]:
    """Validate a game pack and return a human-readable summary."""
    pack = load_game(game_id, data_root)
    game = pack["game"]
    return [
        f"Game: {game.title} ({game.version})",
        f"Pokémon: {len(pack['pokemon'])}",
        f"Moves: {len(pack['moves'])}",
        f"Checkpoints: {len(pack['checkpoints'])}",
        f"Bosses: {len(pack['bosses'])}",
    ]
