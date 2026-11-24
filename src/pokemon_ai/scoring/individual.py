from pathlib import Path

from pokemon_ai.config import PROJECT_ROOT
from pokemon_ai.mechanics.availability import first_reliable_checkpoint
from pokemon_ai.mechanics.evolution import strongest_reachable_form
from pokemon_ai.mechanics.type_chart import effectiveness, load_type_chart
from pokemon_ai.models import Pokemon, ScoreBreakdown, UserSettings
from pokemon_ai.scoring.components import clamp, stats_score
from pokemon_ai.scoring.weights import get_individual_weights


def availability_score(pokemon: Pokemon, game: dict, settings: UserSettings) -> tuple[float, list[str]]:
    encounter = next((item for item in game["encounters"] if item.pokemon_id == pokemon.id), None)
    if encounter is None:
        if "gift" in pokemon.tags or "starter" in pokemon.tags:
            return 60.0, ["No encounter record; starter or gift availability may require game-specific setup"]
        return 0.0, ["No encounter or acquisition record"]
    if encounter.method in {"rare", "optional"} and not settings.optional_encounters_allowed:
        return 20.0, ["Optional encounter excluded by settings"]
    if encounter.encounter_rate < 0.01 and not settings.rare_encounters_allowed:
        return 15.0, ["Rare encounter excluded by settings"]
    if encounter.required_field_move or encounter.required_item:
        resources = encounter.required_field_move or encounter.required_item
        return clamp(encounter.probability_reliability * 85 - encounter.detour_cost), [f"Requires {resources}; reliability {encounter.probability_reliability:.0%}"]
    checkpoint = first_reliable_checkpoint(pokemon.id, game["encounters"], game["checkpoints"])
    if checkpoint is None:
        return 30.0, ["Reliably obtainable status is unknown"]
    remaining = sum(cp.importance for cp in game["checkpoints"] if cp.order >= checkpoint.order)
    total = sum(cp.importance for cp in game["checkpoints"]) or 1.0
    score = clamp(40 + 60 * remaining / total - encounter.detour_cost)
    return score, [f"First reliable acquisition at {checkpoint.name}; encounter reliability {encounter.probability_reliability:.0%}"]


def evolution_score(pokemon: Pokemon, game: dict, settings: UserSettings) -> tuple[float, list[str]]:
    reachable = strongest_reachable_form(pokemon.id, game["pokemon"], game["evolutions"], settings)
    if reachable.id == pokemon.id:
        outgoing = [evo for evo in game["evolutions"] if evo.from_id == pokemon.id]
        if outgoing:
            return 45.0, [f"Evolution blocked or unavailable; strongest reachable form remains {pokemon.species}"]
        return 90.0, ["No evolution required"]
    improvement = reachable.base_stats.total - pokemon.base_stats.total
    return clamp(75 + improvement / 4), [f"Can reach {reachable.species}; final BST improvement {improvement}"]


def movepool_score(pokemon: Pokemon, game: dict, settings: UserSettings) -> tuple[float, list[str]]:
    access = [item for item in game["move_access"] if item.pokemon_id == pokemon.id]
    moves = {item.id: item for item in game["moves"]}
    usable = [moves[item.move_id] for item in access if item.move_id in moves]
    stab = [move for move in usable if move.type in pokemon.types]
    offensive_stab = [move for move in stab if move.category != "status"]
    coverage_types = sorted({move.type for move in usable if move.type not in pokemon.types})
    score = 20 + len(offensive_stab) * 14 + min(len(coverage_types), 3) * 10
    if not usable:
        score = 20
    return clamp(score), [f"{len(offensive_stab)} offensive STAB options and {len(coverage_types)} coverage types"]


def boss_performance_score(pokemon: Pokemon, game: dict, settings: UserSettings) -> tuple[float, list[str]]:
    chart_path = Path(game["type_chart"])
    chart = load_type_chart(chart_path)
    encounter = first_reliable_checkpoint(pokemon.id, game["encounters"], game["checkpoints"])
    if encounter is None:
        return 0.0, ["Unavailable: no acquisition record"]
    reasons: list[str] = []
    weighted = 0.0
    weight_total = 0.0
    for boss in game["bosses"]:
        cp = next((item for item in game["checkpoints"] if item.id == boss.checkpoint_id), None)
        if cp is None or encounter.order > cp.order:
            continue
        cp_matchups = []
        for member in boss.members:
            member_types = member.types or [member.species.lower()]
            incoming = max(effectiveness(chart, attack_type, pokemon.types) for attack_type in member_types)
            outgoing = max(effectiveness(chart, attack_type, member_types) for attack_type in pokemon.types)
            cp_matchups.append((incoming, outgoing))
        pressure = sum(item[1] for item in cp_matchups) / len(cp_matchups)
        safety = sum(1 / item[0] for item in cp_matchups) / len(cp_matchups)
        matchup = clamp((pressure * 45 + safety * 55))
        weighted += matchup * cp.importance
        weight_total += cp.importance
        if pressure >= 2:
            reasons.append(f"Good pressure into {boss.name}")
    return clamp(weighted / weight_total if weight_total else 0), reasons or ["No stronger matchup signal; relies on role and stats"]


def progression_contribution_score(pokemon: Pokemon, game: dict, settings: UserSettings) -> tuple[float, list[str]]:
    encounter = first_reliable_checkpoint(pokemon.id, game["encounters"], game["checkpoints"])
    if encounter is None:
        return 0.0, ["No progression contribution before reaching an acquisition point"]
    boss_score, _ = boss_performance_score(pokemon, game, settings)
    availability, _ = availability_score(pokemon, game, settings)
    weighted = 0.0
    weight_total = 0.0
    for cp in game["checkpoints"]:
        if cp.order >= encounter.order:
            weighted += cp.importance * (availability / 100) * (boss_score / 100) * 100
            weight_total += cp.importance
    score = clamp(weighted / weight_total if weight_total else 0)
    return score, [f"Contributes from {encounter.name} through remaining weighted checkpoints"]


def reliability_score(pokemon: Pokemon, game: dict, settings: UserSettings) -> tuple[float, list[str]]:
    encounter = next((item for item in game["encounters"] if item.pokemon_id == pokemon.id), None)
    reliability = 100.0
    reasons = []
    if encounter:
        reliability = reliability * 0.5 + encounter.probability_reliability * 50
        if encounter.encounter_rate < 0.05:
            reliability -= 20
            reasons.append("Low encounter probability")
    if pokemon.base_stats.hp < 45:
        reliability -= 10
        reasons.append("Low HP may reduce safe switch-ins")
    score = clamp(reliability)
    return score, reasons or ["No major reliability penalty identified"]


def convenience_score(pokemon: Pokemon, game: dict, settings: UserSettings) -> tuple[float, list[str]]:
    encounter = next((item for item in game["encounters"] if item.pokemon_id == pokemon.id), None)
    if encounter is None:
        return 30.0, ["Acquisition convenience unknown"]
    score = clamp(100 - encounter.detour_cost - (0 if settings.optional_encounters_allowed else 10))
    return score, [f"Detour cost {encounter.detour_cost:.1f}; optional encounters are {'allowed' if settings.optional_encounters_allowed else 'excluded'}"]


def score_pokemon(pokemon: Pokemon, game: dict, settings: UserSettings, weights: dict[str, float] | None = None) -> ScoreBreakdown:
    """Return an explainable 0–100 individual rating for a Pokémon."""
    if pokemon.id in settings.banned_pokemon:
        return ScoreBreakdown(total=0, penalties={"banned": 100.0}, reasons=["Banned by settings"], confidence=1.0)
    if "legendary" in pokemon.tags and not settings.legendaries_allowed:
        return ScoreBreakdown(total=0, penalties={"legendary": 100.0}, reasons=["Legendary use excluded"], confidence=1.0)
    if "mythical" in pokemon.tags and not settings.mythicals_allowed:
        return ScoreBreakdown(total=0, penalties={"mythical": 100.0}, reasons=["Mythical use excluded"], confidence=1.0)

    stats, stats_reasons = stats_score(pokemon)
    availability, availability_reasons = availability_score(pokemon, game, settings)
    evolution, evolution_reasons = evolution_score(pokemon, game, settings)
    movepool, movepool_reasons = movepool_score(pokemon, game, settings)
    boss, boss_reasons = boss_performance_score(pokemon, game, settings)
    progression, progression_reasons = progression_contribution_score(pokemon, game, settings)
    reliability, reliability_reasons = reliability_score(pokemon, game, settings)
    convenience, convenience_reasons = convenience_score(pokemon, game, settings)
    components = {
        "stats": stats,
        "availability": availability,
        "evolution": evolution,
        "movepool": movepool,
        "boss_performance": boss,
        "progression": progression,
        "reliability": reliability,
        "convenience": convenience,
    }
    applied_weights = get_individual_weights(weights)
    total = clamp(sum(components[key] * applied_weights[key] for key in applied_weights))
    reasons = stats_reasons + availability_reasons + evolution_reasons + movepool_reasons + boss_reasons + progression_reasons + reliability_reasons + convenience_reasons
    confidence = clamp(game["game"].data_completeness * 100, 0, 100) / 100
    return ScoreBreakdown(total=total, components=components, reasons=reasons, confidence=confidence)
