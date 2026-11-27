from pokemon_ai.models import Checkpoint, MoveAccess


def moves_available_at(pokemon_id: str, checkpoint: Checkpoint, move_access: list[MoveAccess]) -> list[str]:
    """Return move IDs whose source is level-based or unlocked by this checkpoint."""
    available: list[str] = []
    for access in move_access:
        if access.pokemon_id != pokemon_id:
            continue
        if access.source == "level-up":
            if access.level is not None and checkpoint.level_cap is not None and access.level <= checkpoint.level_cap:
                available.append(access.move_id)
            elif access.level is not None and checkpoint.order >= 1:
                available.append(access.move_id)
        elif access.checkpoint == checkpoint.id:
            available.append(access.move_id)
    return available
