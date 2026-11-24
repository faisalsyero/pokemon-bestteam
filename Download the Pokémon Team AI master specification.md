# Pokémon Playthrough Team Optimiser

## Master Build Specification for VS Code Copilot / Coding Agent

You are an expert Python software architect, optimisation engineer, data modeller, test engineer, and Pokémon mechanics analyst.

Your task is to build a complete, extensible Python project that recommends the best team of up to six Pokémon for a main-series Pokémon game or ROM hack playthrough. The system must prioritise whole-playthrough usefulness rather than competitive battling alone.

Work incrementally, keep the project runnable after every phase, and do not replace functioning code with placeholders. When requirements are ambiguous, choose the simplest extensible implementation and document the decision.

---

# 1. Core objective

Build a program that can:

1. Load game-specific Pokémon, encounter, evolution, move, item, checkpoint, boss, and mechanics data.
2. Evaluate each Pokémon's usefulness throughout a playthrough.
3. Generate and rank teams of up to six Pokémon.
4. Build a team around one locked/core Pokémon.
5. Account for when each Pokémon becomes obtainable.
6. Account for trade evolutions and game-specific evolution changes.
7. Account for when moves, TMs, tutors, abilities, forms, and evolution items become available.
8. Evaluate teams against important bosses at the point each battle occurs.
9. Recommend temporary early-game members before the final team is obtainable.
10. Compare several optimisation algorithms.
11. Explain why each Pokémon and moveset was selected.
12. Support standard games first and ROM hacks through separate data packs later.

The final goal is not merely to find the six Pokémon with the highest individual ratings. The goal is to find the team and progression plan that provide the strongest, safest, and most efficient complete playthrough.

---

# 2. Required technology

Use:

- Python 3.12 or later
- Standard library where practical
- `pytest` for tests
- `pydantic` for validated data models
- `pandas` only for analysis/export where it adds value
- `numpy` only when numerical operations justify it
- `requests` or `httpx` for optional API imports
- `typer` for the command-line interface
- `rich` for readable terminal output
- `sqlite3` or SQLAlchemy for the later persistent-data phase
- Google OR-Tools as an optional later optimiser

Do not require machine learning for the first version. Begin with transparent, deterministic scoring and search algorithms.

---

# 3. Project structure

Create this structure:

```text
pokemon-playthrough-ai/
├── README.md
├── pyproject.toml
├── .gitignore
├── src/
│   └── pokemon_ai/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── pokemon.py
│       │   ├── move.py
│       │   ├── evolution.py
│       │   ├── encounter.py
│       │   ├── boss.py
│       │   ├── checkpoint.py
│       │   ├── game.py
│       │   ├── team.py
│       │   └── settings.py
│       ├── data/
│       │   ├── loader.py
│       │   ├── validator.py
│       │   ├── cache.py
│       │   └── importers/
│       │       ├── pokeapi.py
│       │       └── custom_json.py
│       ├── mechanics/
│       │   ├── type_chart.py
│       │   ├── availability.py
│       │   ├── evolution.py
│       │   ├── move_access.py
│       │   ├── stats.py
│       │   ├── damage.py
│       │   └── matchup.py
│       ├── scoring/
│       │   ├── components.py
│       │   ├── individual.py
│       │   ├── team.py
│       │   ├── progression.py
│       │   ├── core_support.py
│       │   ├── weights.py
│       │   └── explanation.py
│       ├── optimisation/
│       │   ├── base.py
│       │   ├── greedy.py
│       │   ├── beam_search.py
│       │   ├── random_search.py
│       │   ├── genetic.py
│       │   ├── simulated_annealing.py
│       │   ├── tabu_search.py
│       │   ├── cp_sat.py
│       │   └── hybrid.py
│       ├── planning/
│       │   ├── roster.py
│       │   ├── temporary_members.py
│       │   ├── route_plan.py
│       │   └── moveset_plan.py
│       └── reporting/
│           ├── console.py
│           ├── json_export.py
│           └── comparison.py
├── data/
│   ├── schemas/
│   └── games/
│       └── demo_game/
│           ├── game.json
│           ├── pokemon.json
│           ├── moves.json
│           ├── encounters.json
│           ├── evolutions.json
│           ├── checkpoints.json
│           ├── bosses.json
│           ├── items.json
│           └── type_chart.json
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

# 4. Development rules

Follow these rules throughout the build:

1. Keep domain models separate from scoring and optimisation.
2. Never hard-code a particular game's rules inside the generic engine.
3. Put game-specific changes in the relevant game data pack.
4. Every public scoring function must return a documented value, normally from 0 to 100.
5. Clamp scores safely and test minimum and maximum behaviour.
6. Do not use one unexplained "magic score". Return a score breakdown.
7. Use type hints on all public functions.
8. Use docstrings for non-obvious logic.
9. Use seeded randomness in stochastic algorithms so results can be reproduced.
10. Validate all loaded game data and give readable error messages.
11. Add tests before moving to the next major phase.
12. Preserve backward compatibility with earlier data packs where reasonable.
13. Record assumptions in `README.md` and code comments.
14. Never claim a team is mathematically optimal unless exhaustive search or an exact solver proves it.
15. Label heuristic results as the best team found within the configured search budget.

---

# 5. Data models

## 5.1 Pokémon

A Pokémon/form record should support:

- unique ID
- species name
- form name
- types
- base stats
- abilities
- evolution family
- growth rate
- gender restrictions where relevant
- held-item requirements
- form-change requirements
- tags such as starter, legendary, mythical, gift, fossil, static encounter

Do not store a single global availability value on the species. Availability belongs to encounters and acquisition methods because the same Pokémon may be available at several points.

## 5.2 Moves

Each move should support:

- name
- type
- category: physical, special, status
- base power
- accuracy
- priority
- PP
- target
- secondary effect metadata
- setup/stat-change metadata
- recovery, status, hazard, screen, weather, terrain, pivot and utility tags

## 5.3 Move access

Represent move access separately:

- level-up
- TM/HM/TR
- tutor
- egg move
- reminder
- pre-evolution-only move
- event/special source
- checkpoint unlocked
- reusable or single-use

## 5.4 Evolution

Represent evolution requirements with structured conditions:

- level
- item
- trade
- trade while holding item
- friendship
- time of day
- location
- move known
- party member/type requirement
- gender
- game-specific custom method

The evaluation must use the selected game's evolution data, not assumptions from the official games.

## 5.5 Encounters and acquisition

Support:

- location
- first accessible checkpoint
- encounter method
- encounter rate
- level range
- version restriction
- gift/trade/static encounter
- required field move or item
- optional detour cost
- probability/reliability

## 5.6 Checkpoints

A checkpoint represents progression and should contain:

- stable ID
- display name
- order/index
- category: route, rival, boss, gym, dungeon, league, champion, postgame
- level cap or expected level
- newly accessible locations
- newly available items/moves/evolutions
- importance weight

## 5.7 Bosses

Each boss team member should contain as much known information as the data pack provides:

- species/form
- level
- ability
- item
- moves
- nature
- EVs/IVs where relevant
- lead/order information where known
- battle rules such as singles, doubles, weather or terrain

## 5.8 User settings

Support:

- game ID and game version
- starter choice
- required/core Pokémon
- banned Pokémon
- trades allowed
- external trading allowed
- trade evolutions patched
- legendaries allowed
- mythicals allowed
- gift Pokémon allowed
- temporary members allowed
- duplicate species allowed
- grinding tolerance
- optional encounters allowed
- rare encounters allowed
- preferred playstyle
- difficulty
- level-cap enforcement
- team size up to six
- optimisation algorithm
- runtime/search budget
- random seed

---

# 6. Score result design

Do not make scoring functions return only a float. Implement a structure similar to:

```python
class ScoreBreakdown(BaseModel):
    total: float
    components: dict[str, float]
    bonuses: dict[str, float]
    penalties: dict[str, float]
    reasons: list[str]
    confidence: float
```

Scores should be explainable. The CLI should be able to show:

```text
Gyarados: 86.4
  Progression contribution: 89.0
  Boss performance:         91.5
  Stats/role efficiency:    87.0
  Accessible movepool:      78.0
  Evolution accessibility:  95.0
  Penalties:                -4.5
```

The exact numbers above are examples only, not expected hard-coded results.

---

# 7. Implementing individual Pokémon scoring

Create `score_pokemon(pokemon, game, settings) -> ScoreBreakdown` as an orchestrator. It must call smaller independent components.

Initial components:

1. `stats_score`
2. `availability_score`
3. `evolution_score`
4. `movepool_score`
5. `boss_performance_score`
6. `progression_contribution_score`
7. `reliability_score`
8. `convenience_score`

Every component must be unit tested.

## 7.1 Stats score

Do not rely only on base-stat total. Evaluate role efficiency.

For an offensive Pokémon, use its better attacking stat rather than punishing it heavily for its unused attacking stat. Include:

- best attacking stat
- speed
- physical bulk
- special bulk
- role balance

Start with a transparent heuristic normalised to 0–100. Keep constants configurable.

Possible initial concept:

```text
best offence: 40%
speed:        20%
physical bulk:15%
special bulk: 15%
HP/general:   10%
```

These are starting weights, not permanent truths.

## 7.2 Availability score

Calculate how much meaningful game content remains when the Pokémon becomes reliably available.

Consider:

- first reliable acquisition checkpoint
- optional detour
- encounter rate
- required resources
- number and importance of remaining checkpoints

Do not double-count availability if progression contribution already assigns zero contribution before acquisition. Keep both values available for explanation, but configure the final aggregation carefully.

## 7.3 Evolution score

Evaluate whether the useful/final form can realistically be reached and when.

Consider:

- required level relative to checkpoint level caps
- trade availability
- whether the game changes trade evolutions
- item availability
- friendship/time/location requirements
- whether the base or middle form is still useful

If an evolution is impossible under current settings, do not always remove the entire line. Evaluate the strongest reachable form.

## 7.4 Movepool score

Only consider moves obtainable by the current checkpoint when calculating a checkpoint score.

Evaluate:

- reliable STAB
- physical/special stat compatibility
- useful coverage
- accuracy
- setup potential
- recovery
- status and utility
- duplicate/redundant coverage
- timing of TM/tutor access
- opportunity cost for single-use resources

Do not simply select four moves with the highest independent score. Use a small moveset optimiser that rewards complementary moves and penalises four moves of the same type or role.

## 7.5 Boss performance

For each relevant boss:

- return zero or "unavailable" before the Pokémon can be obtained
- generate a legal moveset for that checkpoint
- compare offensive pressure
- compare defensive safety
- account for speed
- account for ability/item interactions where implemented
- account for battle format
- produce a 0–100 matchup score and reasons

Begin with type, speed and move-access heuristics. Add damage calculations in a later phase.

## 7.6 Progression contribution

This should become the main measure of playthrough value.

For every important checkpoint:

```text
contribution = availability × checkpoint importance × matchup usefulness
```

If unavailable, contribution is zero. Average using checkpoint importance weights rather than treating every battle identically.

This prevents a late-game Pokémon from receiving an inflated score merely because it performs well in the few battles remaining.

## 7.7 Reliability

Evaluate:

- move accuracy
- encounter reliability
- setup dependence
- severe matchup variance
- reliance on limited resources
- fragility

## 7.8 Convenience

Evaluate optional quality-of-life factors:

- grinding requirement
- evolution effort
- backtracking/detour cost
- rare encounter rate
- friendship requirements
- awkward move acquisition

Keep convenience separate so the user can lower or disable its weight.

---

# 8. Team scoring

Implement `score_team(team, game, settings) -> ScoreBreakdown` separately from individual scoring.

A team score must not be the average of six individual scores.

Include:

1. weighted boss coverage across progression
2. offensive type coverage
3. defensive weakness and resistance distribution
4. role coverage
5. accessible movesets at each checkpoint
6. speed distribution
7. physical/special damage balance
8. shared weaknesses
9. switch-in safety
10. resource conflicts
11. acquisition timing
12. synergy
13. redundancy
14. backup plans

## 8.1 Role coverage

Recognise roles such as:

- immediate physical attacker
- immediate special attacker
- setup sweeper
- bulky attacker
- defensive pivot
- status support
- speed control
- weather/terrain setter
- hazard control where relevant
- early-game carry
- late-game win condition

Do not force competitive roles that are unnecessary for an ordinary playthrough.

## 8.2 Synergy

Support explicit synergy rules:

- weather
- terrain
- screens
- Trick Room
- Intimidate support
- pivoting
- status support
- ability interactions
- immunity-based switching
- setup opportunities

Use data-driven tags/rules rather than long species-specific `if` chains.

## 8.3 Resource conflicts

Penalise cases where multiple members require the same one-use TM, unique evolution item, exclusive fossil, mutually exclusive gift choice, or incompatible version selection.

---

# 9. Build-around-one-Pokémon mode

Add a core mode where one or more Pokémon are locked into every candidate team.

The objective must change from merely maximising general team strength to making the core Pokémon perform as consistently as possible.

Add a core-support score containing:

- core weakness compensation
- answers to core counters
- setup opportunities created
- status/screen/pivot support
- complementary physical/special damage
- performance before the core is obtainable
- backup win condition
- boss coverage for fights the core cannot handle
- avoidance of unnecessary role duplication

The optimiser must never mutate or remove locked members.

Example CLI concept:

```text
pokemon-ai optimise --game platinum --core garchomp --trades false
```

---

# 10. Team progression and temporary members

The system must eventually recommend a roster plan rather than pretending the final six are available from the beginning.

Implement:

- early-game team
- additions by checkpoint
- temporary members
- suggested replacements
- final team completion point
- evolution timing
- move upgrades

Model replacement cost so the system does not constantly change members for tiny score gains.

Example output:

```text
Before Gym 1: Starter, Budew, Starly
After Gym 1: Add Magikarp
After Gym 3: Evolve Magikarp; replace temporary member
After checkpoint X: Add Gible
Before the League: final six completed
```

The example only demonstrates output format. Do not hard-code it.

---

# 11. Optimisation algorithms

Create a common interface:

```python
class Optimiser(ABC):
    @abstractmethod
    def optimise(self, game, settings) -> OptimisationResult:
        ...
```

`OptimisationResult` should include:

- best team found
- score breakdown
- alternative teams
- algorithm
- seed
- runtime
- candidates evaluated
- stopping reason
- whether optimality was proven

Implement in this order:

## 11.1 Exhaustive search for tiny fixtures

Use exhaustive search only on small test pools. It provides a known optimum for validating heuristics.

## 11.2 Random search

Use as a basic benchmark.

## 11.3 Greedy search

Repeatedly add the candidate that increases team score the most. It is a baseline, not the final answer.

## 11.4 Beam search

Start with an empty team or locked core and expand partial teams. Keep the top configurable number after each depth.

Requirements:

- configurable beam width
- duplicate-team prevention
- locked core support
- deterministic tie-breaking
- partial-team scoring
- pruning of impossible teams

## 11.5 Genetic algorithm

Represent a team as a chromosome.

Include:

- valid population initialisation
- tournament or rank selection
- crossover without duplicates
- mutation respecting locks/bans
- elitism
- reproducible seed
- generation and stagnation limits

## 11.6 Simulated annealing

Use legal one-member swaps and configurable cooling. Permit occasional worse moves to escape local optima.

## 11.7 Tabu search

Track recent swaps/team signatures to prevent cycling.

## 11.8 CP-SAT

Add later for constraints that can be modelled cleanly. Do not force every non-linear synergy rule into the exact model. It is acceptable to use CP-SAT for candidate selection followed by heuristic re-ranking.

## 11.9 Hybrid optimiser

Implement after the others work:

1. filter clearly unusable candidates
2. create strong candidates with beam search
3. diversify/refine with a genetic algorithm
4. improve finalists with tabu search or simulated annealing
5. run detailed checkpoint evaluation on finalists

---

# 12. Ratings and later tuning

Design ratings so they can improve without breaking the architecture.

## 12.1 Configurable weights

Store weights in configuration, for example:

```json
{
  "individual": {
    "progression": 0.40,
    "boss_performance": 0.20,
    "movepool": 0.15,
    "stats": 0.10,
    "evolution": 0.05,
    "reliability": 0.05,
    "convenience": 0.05
  }
}
```

Validate that applicable weights sum to 1.0.

## 12.2 Difficulty profiles

Support profiles such as:

- casual
- normal
- hard
- hardcore
- minimal grinding
- speed-oriented
- safest
- offensive
- core-abuse

Profiles change weights and constraints, not core code.

## 12.3 Rating calibration

Later, support a calibration dataset containing:

- human-rated Pokémon
- human-rated teams
- game and settings
- rationale/tags
- optional pairwise preferences such as Team A preferred over Team B

Add evaluation tools that calculate:

- ranking correlation
- top-k agreement
- pairwise accuracy
- score error
- optimiser repeatability
- performance by game phase

Do not silently train weights on test data. Keep train, validation and test sets separate if learned tuning is added.

## 12.4 User feedback

Prepare an optional future format for:

- suggested team accepted/rejected
- replacements made by user
- reported difficult bosses
- final completion result
- subjective enjoyment rating

Do not use feedback automatically until validation, privacy and bias concerns are addressed.

## 12.5 Confidence score

A recommendation's confidence should decrease when:

- encounter data is incomplete
- boss movesets are unknown
- move availability is uncertain
- mechanics are approximated
- too few optimisation runs were completed

Do not pretend incomplete ROM-hack data is exact.

---

# 13. Battle and damage evaluation update

After heuristic matchups work, add generation-aware damage estimation.

Requirements:

- level
- move power
- Attack or Special Attack
- Defence or Special Defence
- STAB
- type effectiveness
- random damage range
- critical-hit rules by generation where needed
- weather
- screens
- abilities
- held items
- spread-move modifier
- generation/game-specific overrides

Keep this module isolated because ROM hacks may change mechanics.

Do not immediately build a perfect turn-by-turn simulator. First calculate useful features such as:

- expected damage percentage
- probable hits to KO
- whether the attacker is faster
- expected damage received
- safe switch-in estimate
- setup opportunity estimate

Later, a limited battle search can model setup, healing and switching for important bosses.

---

# 14. Data import

## 14.1 Demo data

Begin with a fictional or small manually verified demo game containing approximately 10–20 Pokémon and several bosses. This keeps tests manageable.

## 14.2 Standard-game data

Add an optional importer for public standard Pokémon data. Cache responses locally and transform external records into the project's internal schema.

Do not make the engine depend directly on an external API at runtime.

## 14.3 ROM hacks

Treat every ROM hack as a separate versioned data pack.

Each pack should include:

- title
- version
- base game/generation
- supported difficulty
- source notes
- data completeness
- mechanics overrides
- altered species/types/stats/abilities
- altered moves
- altered evolution methods
- encounters
- bosses
- items/TMs/tutors

Never mix data from two versions of the same hack without warning.

---

# 15. Testing requirements

Use `pytest`.

Required unit tests include:

- score clamping
- stats score for physical and special attackers
- unavailable Pokémon contribution equals zero
- trade evolution unavailable/available behaviour
- game-specific non-trade evolution override
- move legality by checkpoint
- STAB and type effectiveness
- redundant moveset penalty
- shared-weakness penalty
- locked core never removed
- banned Pokémon never selected
- no accidental duplicate species
- deterministic output with a fixed seed
- resource-conflict detection
- malformed data rejection

Required integration tests include:

- load complete demo game
- score all Pokémon
- generate a team with greedy search
- generate a team with beam search
- build around a locked core
- export results to JSON
- compare optimiser result with exhaustive optimum on a tiny fixture

Add performance tests only after correctness tests pass.

---

# 16. CLI requirements

Implement commands similar to:

```text
pokemon-ai validate-data --game demo_game
pokemon-ai rank-pokemon --game demo_game
pokemon-ai score-pokemon --game demo_game --pokemon gyarados
pokemon-ai score-team --game demo_game --team a,b,c,d,e,f
pokemon-ai optimise --game demo_game --algorithm beam
pokemon-ai optimise --game demo_game --core garchomp --trades false
pokemon-ai compare-algorithms --game demo_game --seed 42
pokemon-ai progression-plan --game demo_game --team a,b,c,d,e,f
```

Every command must provide useful errors for unknown games, Pokémon or invalid settings.

---

# 17. Reporting requirements

For the best result, display:

1. game and settings
2. final team
3. overall score
4. score breakdown
5. each member's role
6. why each member was selected
7. availability and evolution timing
8. recommended checkpoint-legal moveset
9. boss strengths
10. difficult matchups
11. temporary-member/progression plan
12. alternative teams
13. algorithm and runtime
14. confidence and known data limitations

Do not output vague claims such as "great coverage" without showing which useful types or bosses are covered.

---

# 18. Implementation phases

Complete the project in phases. At the end of every phase:

- run tests
- fix failures
- update the README
- show files created/changed
- explain major decisions
- give exact commands to run the current version

## Phase 1: Foundation

- initialise project
- configuration
- Pydantic domain models
- JSON loader and validation
- small demo dataset
- type chart
- basic CLI
- tests

## Phase 2: Individual scoring

- stats
- availability
- evolution
- basic legal movepool
- basic boss matchup
- progression contribution
- explainable breakdown
- tests

## Phase 3: Team scoring

- offensive/defensive coverage
- shared weaknesses
- roles
- physical/special balance
- simple synergy/redundancy
- resource conflicts
- tests

## Phase 4: First optimisation

- exhaustive tiny-fixture search
- random baseline
- greedy
- beam search
- locked-core mode
- benchmarks

## Phase 5: Progression planning

- temporary members
- replacement cost
- roster by checkpoint
- move/evolution progression
- tests

## Phase 6: Advanced optimisation

- genetic algorithm
- simulated annealing
- tabu search
- algorithm comparison
- hybrid optimiser

## Phase 7: Detailed battle evaluation

- generation-aware damage features
- checkpoint-legal movesets
- improved boss scoring
- confidence tracking

## Phase 8: Data expansion

- standard-game importer
- caching
- game data-pack documentation
- first fully supported real game

## Phase 9: Ratings and calibration

- externalised weights
- profiles
- human rating dataset schema
- evaluation metrics
- weight-tuning experiment

## Phase 10: Interface

Only after the engine is tested, add either:

- a FastAPI backend and simple web UI, or
- a desktop UI

Do not couple the UI to optimisation internals.

---

# 19. Immediate first assignment

Begin by completing Phase 1 and the smallest useful part of Phase 2.

Specifically:

1. Create the full project skeleton.
2. Configure packaging and dependencies.
3. Implement validated models for Pokémon, moves, encounters, evolutions, checkpoints, bosses, games, teams and settings.
4. Create a demo dataset with 10–20 Pokémon and at least four weighted boss checkpoints.
5. Implement a type chart loader.
6. Implement `stats_score`, `availability_score`, `evolution_score`, and an initial `score_pokemon` orchestrator.
7. Return `ScoreBreakdown`, not a raw unexplained number.
8. Add CLI commands to validate data and rank Pokémon.
9. Add unit and integration tests.
10. Run the test suite and fix all failures.
11. Update `README.md` with setup and usage.

Do not implement genetic algorithms, detailed damage simulation, a web UI or hundreds of Pokémon yet. Build a correct, understandable foundation first.

---

# 20. Definition of done for the first assignment

The first assignment is complete when all of the following are true:

- a fresh virtual environment can install the project
- `pytest` passes
- demo data validates
- the CLI ranks demo Pokémon
- each rating includes a component breakdown
- trade evolution settings affect reachable-form scoring
- unavailable Pokémon are penalised correctly
- all major constants are configurable
- the README gives exact setup and run commands
- no unfinished `pass`, fake implementation or unexplained placeholder remains in completed Phase 1/2 code

Now inspect the current workspace. If it is empty, initialise the project. If files already exist, preserve compatible work and refactor carefully. Complete only the immediate first assignment, then report what was built, tests run, assumptions made, and the next recommended phase.
