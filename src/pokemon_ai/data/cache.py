import json
from pathlib import Path


class JsonCache:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict | None:
        path = self.directory / f"{key}.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def set(self, key: str, value: dict) -> None:
        path = self.directory / f"{key}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
