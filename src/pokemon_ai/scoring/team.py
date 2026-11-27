from collections import Counter

from pokemon_ai.models import Pokemon, ScoreBreakdown, Team, UserSettings
from pokemon_ai.scoring.components import clamp
from pokemon_ai.scoring.individual import score_pokemon


def infer_roles(pokemon: Pokemon) -> list[str]:
    stats = pokemon.base_stats
    roles: list[str] = []
    if max(stats.attack, stats.special_attack) >= 100:
        roles.append("attacker")
    if stats.speed >= 90:
        roles.append("speed_control")
    if stats.hp + stats.defense >= 170:
        roles.append("physical_wall")
    if stats.hp + stats.special_defense >= 170:
        roles.append("special_wall")
    if not roles:
        roles.append("balanced_support")
    return roles


def score_team(team: Team, game: dict, settings: UserSettings) -> ScoreBreakdown:
    """Score team synergy and progression coverage, not a simple member average."""
    by_id = {pokemon.id: pokemon for pokemon in game["pokemon"]}
    members = [by_id[pokemon_id] for pokemon_id in team.pokemon_ids if pokemon_id in by_id]
    if not members:
        return ScoreBreakdown(total=0, penalties={"empty_team": 100}, reasons=["Team has no valid members"], confidence=0)

    individual = [score_pokemon(pokemon, game, settings) for pokemon in members]
    average = sum(score.total for score in individual) / len(individual)

    type_counts = Counter(type_name for pokemon in members for type_name in pokemon.types)
    coverage = len(type_counts)
    coverage_score = clamp(coverage / 6 * 100)

    weaknesses: Counter[str] = Counter()
    for boss in game["bosses"]:
        for member in boss.members:
            for defender in members:
                defending_types = set(defender.types)
                for attacker_type in member.types or [member.species.lower()]:
                    chart = game["_chart"]
                    weakness = chart.get(attacker_type.lower(), {}).get(next(iter(defending_types)), 1)
                    if weakness >= 2:
                        weaknesses[attacker_type] += 1
    shared_penalty = clamp(sum(count - 1 for count in weaknesses.values()) * 4)
    shared_score = clamp(100 - shared_penalty)

    roles = {role for member in members for role in infer_roles(member)}
    role_score = clamp(len(roles) / 5 * 100)

    species_penalty = len(team.pokemon_ids) - len(set(pokemon.species for pokemon in members))
    species_score = clamp(100 - species_penalty * 20)

    resource_penalty = 0.0
    move_sources: Counter[str] = Counter()
    for member in members:
        for access in game["move_access"]:
            if access.pokemon_id == member.id and access.source.lower() in {"tm", "tr", "tutor"}:
                move_sources[access.move_id] += 1
    resource_penalty = clamp(sum(count - 1 for count in move_sources.values()) * 10)

    boss_score = 0.0
    boss_weight = 0.0
    for boss in game["bosses"]:
        cp = next((item for item in game["checkpoints"] if item.id == boss.checkpoint_id), None)
        if cp is None:
            continue
        boss_matches = []
        for member in members:
            member_scores = [
                sum(1.0 for attack_type in boss_member.types or [boss_member.species.lower()]
                    for pokemon_type in member.types
                    if game["_chart"].get(attack_type.lower(), {}).get(pokemon_type, 1) >= 2)
                for boss_member in boss.members
            ]
            boss_matches.append(sum(member_scores) / max(1, len(boss_members := boss.members)))
        boss_score += (100 - min(100, sum(boss_matches) * 8)) * cp.importance
        boss_weight += cp.importance
    boss_coverage = clamp(boss_score / boss_weight if boss_weight else 0)

    core_bonus = 0.0
    core_reasons: list[str] = []
    for core_id in settings.core_pokemon:
        if core_id not in team.pokemon_ids:
            return ScoreBreakdown(total=0, penalties={"missing_core": 100}, reasons=[f"Locked core {core_id} is missing"], confidence=0)
        core = by_id.get(core_id)
        if core:
            support_types = {type_name for member in members if member.id != core_id for type_name in member.types}
            core_bonus = clamp(len(support_types) / 6 * 20)
            core_reasons.append(f"Core {core.species} is locked and supported by {len(support_types)} additional types")

    total = clamp(
        average * 0.30
        + boss_coverage * 0.20
        + coverage_score * 0.15
        + shared_score * 0.15
        + role_score * 0.10
        + species_score * 0.05
        + core_bonus
        - resource_penalty * 0.05
    )
    reasons = [
        f"Member average: {average:.1f}",
        f"Defensive type diversity: {coverage}/6",
        f"Role diversity: {', '.join(sorted(roles))}",
        f"Shared-weakness score: {shared_score:.1f}",
        f"Single-use move resource conflicts: {resource_penalty:.1f}",
        *core_reasons,
    ]
    return ScoreBreakdown(
        total=total,
        components={
            "member_average": average,
            "boss_coverage": boss_coverage,
            "offensive_type_coverage": coverage_score,
            "shared_weakness_resistance": shared_score,
            "role_coverage": role_score,
            "species_diversity": species_score,
        },
        penalties={"resource_conflicts": resource_penalty},
        bonuses={"core_support": core_bonus},
        reasons=reasons,
        confidence=sum(score.confidence for score in individual) / len(individual),
    )
