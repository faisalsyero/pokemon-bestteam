from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    game_id: str
    game_version: str = "default"
    starter_choice: str | None = None
    core_pokemon: list[str] = Field(default_factory=list)
    banned_pokemon: list[str] = Field(default_factory=list)
    trades_allowed: bool = False
    external_trading_allowed: bool = False
    trade_evolutions_patched: bool = False
    legendaries_allowed: bool = True
    mythicals_allowed: bool = False
    gift_pokemon_allowed: bool = True
    temporary_members_allowed: bool = True
    duplicate_species_allowed: bool = False
    grinding_tolerance: float = Field(ge=0, le=1, default=0.5)
    optional_encounters_allowed: bool = True
    rare_encounters_allowed: bool = True
    preferred_playstyle: str = "normal"
    difficulty: str = "normal"
    level_cap_enforcement: bool = True
    team_size: int = Field(ge=1, le=6, default=6)
    optimisation_algorithm: str = "greedy"
    runtime_seconds: float = Field(gt=0, default=30)
    random_seed: int = 42
