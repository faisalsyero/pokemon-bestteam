from pydantic import BaseModel, Field


class Team(BaseModel):
    pokemon_ids: list[str] = Field(min_length=1, max_length=6)
