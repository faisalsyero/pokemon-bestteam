from pokemon_ai.data.loader import load_game


def load_custom_pack(game_id: str, data_root: str) -> dict:
    """Load a custom game pack through the standard validated loader."""
    return load_game(game_id, data_root)
