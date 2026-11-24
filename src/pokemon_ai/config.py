from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INDIVIDUAL_WEIGHTS = {
    "progression": 0.40,
    "boss_performance": 0.20,
    "movepool": 0.10,
    "stats": 0.10,
    "evolution": 0.05,
    "availability": 0.05,
    "reliability": 0.05,
    "convenience": 0.05,
}
