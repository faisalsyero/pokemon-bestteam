# Pokémon Playthrough Team Optimiser

This repository contains Phase 1 (foundation) and the smallest useful Phase 2
(individual Pokémon scoring) implementation of the master specification.

## Requirements

- Python 3.12 or later
- `pytest`, `pydantic`, `typer`, and `rich`

The project was validated with Python 3.13 on Windows.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

The editable install provides the `pokemon-ai` command.

## Demo data

The fictional `demo_game` pack contains 12 Pokémon, 12 moves, 4 weighted
checkpoints, and 4 bosses. Packs live under `data/games/<game-id>/`.

## Run

```powershell
pokemon-ai validate-data --game demo_game
pokemon-ai rank-pokemon --game demo_game
pokemon-ai score-pokemon --game demo_game --pokemon voltkit
pokemon-ai score-team --game demo_game --team brookfin,sparrow,grotto,voltkit,mossling,puddle
pokemon-ai optimise --game demo_game --algorithm beam --seed 42
py -m pokemon_ai optimise --game demo_game --algorithm beam --core voltkit --trades
pokemon-ai compare-algorithms --game demo_game --seed 42
pokemon-ai progression-plan --game demo_game --team brookfin,sparrow,grotto,voltkit,mossling,puddle
pytest -q
```

You can also run the CLI without the console script:

```powershell
python -m pokemon_ai.cli validate-data --game demo_game
```

## Web UI

Start the easy browser interface:

```powershell
python -m pokemon_ai.web
# or
pokemon-team-ui
```

Open `http://127.0.0.1:8000`. It provides:

- A selectable Pokémon roster
- Manual team selection and team scoring
- Pokémon rankings
- Trade, core, banned-Pokémon, seed, team-size, and algorithm controls
- Best-team, explanation, and alternative-team results

The API is available at `/api/games`, `/api/pokemon`, `/api/rank`,
`/api/score-team`, and `/api/optimise`.

## Implemented in this phase

- Pydantic models for games, Pokémon, moves, move access, evolutions,
  encounters, checkpoints, bosses, teams, settings, and score breakdowns
- JSON loading and validation with readable unknown/malformed data errors
- Generation-independent type-chart loading
- Availability, evolution, stats, basic movepool, boss, progression,
  reliability, and convenience components
- Explainable 0–100 `ScoreBreakdown` aggregation with configurable weights
- Trade-evolution and trade-patched behaviour
- CLI validation, ranking, and per-Pokémon reporting
- Unit and integration tests for the demo pack
- Team-level type, boss, role, resource, species, and core-synergy scoring
- Exhaustive, random, greedy, beam, genetic, simulated-annealing, tabu, and hybrid optimisers
- Seeded and core-aware deterministic search
- Progression roster plans and moveset checkpoint helpers
- Generation-aware heuristic damage features
- PokeAPI cached import scaffolding and custom JSON loading
- FastAPI JSON API and a dark, easy-to-use browser UI
- Difficulty profiles and calibration data schemas

## Assumptions

- Trade evolutions require trades plus external trading by default. Setting
  `trade_evolutions_patched=true` makes a patched trade evolution reachable.
- Boss matchups use transparent type, pressure, and safety heuristics rather than
  a turn-by-turn damage engine.
- Demo data is fictional and has a confidence value below 1.0.
- This phase does not implement team optimisation, damage simulation, or
  later optimisation algorithms.

## Next phase

Phase 3 can build team-level scoring on top of the current individual scorer,
followed by Phase 4 greedy and beam optimisers.