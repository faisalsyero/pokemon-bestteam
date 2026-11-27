import requests

from pokemon_ai.data.cache import JsonCache


def fetch_pokemon(name: str, cache_directory: str = ".cache/pokeapi") -> dict:
    """Fetch public PokeAPI species data and cache it locally."""
    cache = JsonCache(cache_directory)
    key = name.lower().strip()
    cached = cache.get(key)
    if cached is not None:
        return cached
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{key}", timeout=15)
    response.raise_for_status()
    result = response.json()
    cache.set(key, result)
    return result


def transform_pokemon(record: dict) -> dict:
    stats = {item["stat"]["name"]: item["base_stat"] for item in record["stats"]}
    return {
        "id": record["name"],
        "species": record["name"].title(),
        "form": "default",
        "types": [item["type"]["name"] for item in record["types"]],
        "base_stats": {
            "hp": stats["hp"],
            "attack": stats["attack"],
            "defense": stats["defense"],
            "special_attack": stats["special-attack"],
            "special_defense": stats["special-defense"],
            "speed": stats["speed"],
        },
        "abilities": [item["ability"]["name"] for item in record["abilities"]],
        "evolution_family": record["name"],
    }
