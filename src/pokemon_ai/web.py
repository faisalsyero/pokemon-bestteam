from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from pokemon_ai.data.loader import load_game
from pokemon_ai.models import Team, UserSettings
from pokemon_ai.optimisation.advanced import (
    GeneticOptimiser,
    HybridOptimiser,
    SimulatedAnnealingOptimiser,
    TabuOptimiser,
)
from pokemon_ai.optimisation.search import BeamSearchOptimiser, ExhaustiveOptimiser, GreedyOptimiser, RandomOptimiser
from pokemon_ai.scoring.individual import score_pokemon
from pokemon_ai.scoring.team import score_team

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
app = FastAPI(title="Pokémon Playthrough Team Optimiser", version="0.2.0")


class OptimiseRequest(BaseModel):
    game: str = "demo_game"
    algorithm: Literal["exhaustive", "random", "greedy", "beam", "genetic", "simulated_annealing", "tabu", "hybrid"] = "beam"
    core: list[str] = []
    banned: list[str] = []
    trades: bool = False
    team_size: int = 6
    seed: int = 42


class TeamRequest(BaseModel):
    game: str = "demo_game"
    team: list[str]


def get_pack(game_id: str) -> dict:
    try:
        return load_game(game_id, DATA_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/games")
def games() -> list[dict]:
    games_root = DATA_ROOT / "games"
    output = []
    for path in sorted(games_root.iterdir()):
        if path.is_dir():
            pack = get_pack(path.name)
            output.append({
                "id": pack["game"].id,
                "title": pack["game"].title,
                "pokemon_count": len(pack["pokemon"]),
            })
    return output


@app.get("/api/pokemon")
def pokemon(game: str = "demo_game") -> list[dict]:
    pack = get_pack(game)
    return [
        {
            "id": item.id,
            "name": item.display_name or item.species,
            "types": item.types,
            "tags": item.tags,
        }
        for item in pack["pokemon"]
    ]


@app.get("/api/rank")
def rank(game: str = "demo_game", trades: bool = False) -> list[dict]:
    pack = get_pack(game)
    settings = UserSettings(
        game_id=game,
        trades_allowed=trades,
        external_trading_allowed=trades,
    )
    rows = []
    for member in pack["pokemon"]:
        result = score_pokemon(member, pack, settings)
        rows.append({"pokemon": member.id, "name": member.display_name or member.species, "score": result, "types": member.types})
    return sorted(rows, key=lambda item: (-item["score"].total, item["pokemon"]))


@app.post("/api/score-team")
def api_score_team(request: TeamRequest) -> dict:
    pack = get_pack(request.game)
    unknown = [item for item in request.team if item not in {pokemon.id for pokemon in pack["pokemon"]}]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown Pokémon: {', '.join(unknown)}")
    settings = UserSettings(game_id=request.game)
    result = score_team(Team(pokemon_ids=request.team), pack, settings)
    return result.model_dump(mode="json")


@app.post("/api/optimise")
def api_optimise(request: OptimiseRequest) -> dict:
    pack = get_pack(request.game)
    pokemon_ids = {pokemon.id for pokemon in pack["pokemon"]}
    unknown = [item for item in request.core + request.banned if item not in pokemon_ids]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown Pokémon: {', '.join(unknown)}")
    settings = UserSettings(
        game_id=request.game,
        core_pokemon=request.core,
        banned_pokemon=request.banned,
        trades_allowed=request.trades,
        external_trading_allowed=request.trades,
        team_size=request.team_size,
        random_seed=request.seed,
    )
    optimisers = {
        "exhaustive": ExhaustiveOptimiser(),
        "random": RandomOptimiser(),
        "greedy": GreedyOptimiser(),
        "beam": BeamSearchOptimiser(),
        "genetic": GeneticOptimiser(),
        "simulated_annealing": SimulatedAnnealingOptimiser(),
        "tabu": TabuOptimiser(),
        "hybrid": HybridOptimiser(),
    }
    result = optimisers[request.algorithm].optimise(pack, settings)
    return result.model_dump(mode="json")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pokémon Playthrough Team Optimiser</title>
  <style>
    :root{color-scheme:dark;--bg:#09111f;--panel:#111d30;--line:#263650;--accent:#78d6a7;--gold:#f4c95d}
    *{box-sizing:border-box} body{margin:0;font-family:Inter,Segoe UI,sans-serif;background:var(--bg);color:#edf4ff}
    header{padding:24px max(24px,calc((100% - 1100px)/2));border-bottom:1px solid var(--line);background:#0d1728}
    h1{margin:0;font-size:24px}.wrap{max-width:1100px;margin:auto;padding:24px}.grid{display:grid;grid-template-columns:280px 1fr;gap:18px}
    .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}.row{display:flex;gap:10px;flex-wrap:wrap}
    label{display:block;margin:12px 0 6px;color:#b9c7dc;font-size:13px}select,input,button{font:inherit}
    select,input{width:100%;padding:10px;border-radius:8px;border:1px solid var(--line);background:#0b1424;color:white}
    button{border:0;border-radius:9px;padding:11px 14px;background:var(--accent);color:#092016;font-weight:700;cursor:pointer}
    button.secondary{background:#273950;color:white}.pokemon-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:9px;max-height:420px;overflow:auto}
    .pokemon{border:1px solid var(--line);border-radius:10px;padding:10px;background:#0c1627;cursor:pointer}.pokemon.selected{border-color:var(--accent);background:#102c2b}
    .score{float:right;color:var(--gold);font-weight:800}.team{margin-top:12px;padding:12px;border-radius:10px;background:#0b1424;min-height:60px}
    .type{display:inline-block;padding:2px 7px;margin:2px;border-radius:99px;background:#263950;font-size:11px}
    .result{white-space:pre-wrap;line-height:1.6}table{width:100%;border-collapse:collapse}td,th{padding:9px;border-bottom:1px solid var(--line);text-align:left}
    @media(max-width:800px){.grid{grid-template-columns:1fr}.wrap{padding:14px}}
  </style>
</head>
<body><header><h1>Pokémon Playthrough Team Optimiser</h1></header>
<main class="wrap"><div class="grid">
<aside class="card"><label>Game pack</label><select id="game"></select>
<label>Optimiser</label><select id="algorithm"><option>beam</option><option>greedy</option><option>random</option><option>genetic</option><option>simulated_annealing</option><option>tabu</option><option>hybrid</option><option>exhaustive</option></select>
<label>Seed</label><input id="seed" type="number" value="42">
<label>Team size</label><input id="size" type="number" min="1" max="6" value="6">
<label><input id="trades" type="checkbox" style="width:auto"> Trades allowed</label>
<div class="row" style="margin-top:14px"><button id="optimise">Find team</button><button id="clear" class="secondary">Clear</button></div>
<div class="team" id="team">Selected team: none</div></aside>
<section><div class="card"><div class="row" style="justify-content:space-between"><strong>Pokémon roster</strong><button id="rank" class="secondary">Rank all</button></div><div id="roster" class="pokemon-grid" style="margin-top:12px"></div></div>
<div class="card" style="margin-top:18px"><strong>Explanation</strong><div id="result" class="result" style="margin-top:10px">Choose a Pokémon or run an optimiser.</div></div></section>
</div></main>
<script>
let selected=[];const $=id=>document.getElementById(id);
async function loadGames(){const games=await (await fetch('/api/games')).json();$('game').innerHTML=games.map(g=>`<option value="${g.id}">${g.title}</option>`).join('');loadRoster()}
async function loadRoster(){const game=$('game').value;const members=await (await fetch('/api/pokemon?game='+encodeURIComponent(game))).json();$('roster').innerHTML=members.map(p=>`<div class="pokemon ${selected.includes(p.id)?'selected':''}" data-id="${p.id}"><strong>${p.name}</strong><br>${p.types.map(t=>`<span class="type">${t}</span>`).join('')}</div>`).join('');document.querySelectorAll('.pokemon').forEach(el=>el.onclick=()=>toggle(el.dataset.id))}
function toggle(id){selected=selected.includes(id)?selected.filter(x=>x!==id):(selected.length<6?[...selected,id]:selected);$('team').textContent='Selected team: '+(selected.join(', ')||'none');loadRoster()}
$('clear').onclick=()=>{selected=[];$('team').textContent='Selected team: none';loadRoster()}
$('game').onchange=()=>{selected=[];loadRoster()}
$('rank').onclick=async()=>{const game=$('game').value;const data=await (await fetch('/api/rank?game='+encodeURIComponent(game)+'&trades='+$('trades').checked)).json();$('result').innerHTML='<table><tr><th>Pokémon</th><th>Score</th></tr>'+data.map(x=>`<tr><td>${x.name}</td><td>${x.score.total.toFixed(1)}</td></tr>`).join('')+'</table>'}
$('optimise').onclick=async()=>{const body={game:$('game').value,algorithm:$('algorithm').value,core:selected,trades:$('trades').checked,team_size:Number($('size').value),seed:Number($('seed').value)};$('result').textContent='Searching…';const r=await fetch('/api/optimise',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok){$('result').textContent=d.detail||'Search failed';return}selected=d.best_team;$('team').textContent='Selected team: '+selected.join(', ');$('result').innerHTML=`<strong>Best team:</strong> ${d.best_team.join(', ')}<br><strong>Score:</strong> ${d.score_breakdown.total.toFixed(1)}<br><strong>Algorithm:</strong> ${d.algorithm}<br><strong>Proven optimal:</strong> ${d.optimality_proven?'Yes':'No'}<br><strong>Reasons:</strong><br>${d.score_breakdown.reasons.map(x=>'• '+x).join('<br>')}<br><strong>Alternatives:</strong><br>${d.alternative_teams.map(x=>'• '+x.join(', ')).join('<br>')}`;loadRoster()}
loadGames();
</script></body></html>"""
    return HTMLResponse(content=html)


def main() -> None:
    import uvicorn
    uvicorn.run("pokemon_ai.web:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
