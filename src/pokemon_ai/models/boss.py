from pydantic import BaseModel, Field


class BossMember(BaseModel):
    species: str
    form: str = "default"
    level: int
    types: list[str] | None = None
    ability: str | None = None
    item: str | None = None
    moves: list[str] = Field(default_factory=list)
    nature: str | None = None
    evs: dict[str, int] = Field(default_factory=dict)
    ivs: dict[str, int] = Field(default_factory=dict)
    lead: bool = False


class Boss(BaseModel):
    id: str
    name: str
    checkpoint_id: str
    members: list[BossMember]
    battle_format: str = "singles"
    weather: str | None = None
    terrain: str | None = None
    rules: list[str] = Field(default_factory=list)
