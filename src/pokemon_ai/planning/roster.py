from pokemon_ai.models import Team, UserSettings
from pokemon_ai.scoring.individual import score_pokemon


def build_roster_plan(team: Team, game: dict, settings: UserSettings) -> list[dict]:
    by_id = {pokemon.id: pokemon for pokemon in game["pokemon"]}
    encounter_by_id = {encounter.pokemon_id: encounter for encounter in game["encounters"]}
    plan: list[dict] = []
    for checkpoint in game["checkpoints"]:
        available = []
        for pokemon_id in team.pokemon_ids:
            pokemon = by_id.get(pokemon_id)
            encounter = encounter_by_id.get(pokemon_id)
            if pokemon and encounter:
                cp = next((item for item in game["checkpoints"] if item.id == encounter.first_checkpoint), None)
                if cp and cp.order <= checkpoint.order:
                    score = score_pokemon(pokemon, game, settings)
                    available.append({"pokemon_id": pokemon_id, "score": round(score.total, 1)})
        plan.append({
            "checkpoint_id": checkpoint.id,
            "name": checkpoint.name,
            "available_team_members": available,
            "temporary_member_needed": len(available) < 3,
        })
    return plan
