import json
from pathlib import Path
from typing import Any


def export_json(result: Any, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
