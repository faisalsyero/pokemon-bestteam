from pokemon_ai.models import Evolution, Pokemon, UserSettings


def can_reach_evolution(evolution: Evolution, settings: UserSettings) -> bool:
    condition = evolution.condition
    if condition.trade or condition.trade_holding_item:
        return bool(settings.trade_evolutions_patched or (settings.trades_allowed and settings.external_trading_allowed))
    if condition.friendship:
        return True
    if condition.location or condition.move_known or condition.party_member or condition.party_type or condition.gender:
        return True
    return True


def strongest_reachable_form(pokemon_id: str, pokemon: list[Pokemon], evolutions: list[Evolution], settings: UserSettings) -> Pokemon:
    by_id = {item.id: item for item in pokemon}
    if pokemon_id not in by_id:
        raise ValueError(f"Unknown Pokémon '{pokemon_id}'")
    current = by_id[pokemon_id]
    while True:
        outgoing = [evo for evo in evolutions if evo.from_id == current.id and can_reach_evolution(evo, settings)]
        if not outgoing:
            return current
        target = by_id[outgoing[0].to_id]
        if target.base_stats.total <= current.base_stats.total:
            return current
        current = target
