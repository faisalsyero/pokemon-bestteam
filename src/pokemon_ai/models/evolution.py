from pydantic import BaseModel, Field


class EvolutionCondition(BaseModel):
    level: int | None = None
    item: str | None = None
    trade: bool = False
    trade_holding_item: str | None = None
    friendship: bool = False
    time_of_day: str | None = None
    location: str | None = None
    move_known: str | None = None
    party_member: str | None = None
    party_type: str | None = None
    gender: str | None = None
    custom_method: str | None = None


class Evolution(BaseModel):
    from_id: str
    to_id: str
    condition: EvolutionCondition = Field(default_factory=EvolutionCondition)
