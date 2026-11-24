from pokemon_ai.models import Encounter, Checkpoint, UserSettings


def first_reliable_checkpoint(pokemon_id: str, encounters: list[Encounter], checkpoints: list[Checkpoint]) -> Checkpoint | None:
    matching = [enc for enc in encounters if enc.pokemon_id == pokemon_id and enc.probability_reliability >= 0.25]
    if not matching:
        return None
    checkpoint_ids = {enc.first_checkpoint for enc in matching}
    candidates = [cp for cp in checkpoints if cp.id in checkpoint_ids]
    return min(candidates, key=lambda cp: cp.order) if candidates else None
