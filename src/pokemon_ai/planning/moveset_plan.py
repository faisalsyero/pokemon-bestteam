from pokemon_ai.mechanics.move_access import moves_available_at
from pokemon_ai.models import Checkpoint


def plan_moveset(pokemon_id: str, checkpoints: list[Checkpoint], move_access: list[dict], moves: dict) -> list[dict]:
    plan = []
    for checkpoint in checkpoints:
        ids = moves_available_at(pokemon_id, checkpoint, move_access)
        plan.append({
            "checkpoint": checkpoint.name,
            "moves": [moves[move_id].name for move_id in ids if move_id in moves],
        })
    return plan
