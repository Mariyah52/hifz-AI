from pydantic import BaseModel, ConfigDict


def to_camel(snake: str) -> str:
    parts = snake.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    """
    Every schema in this app extends this instead of BaseModel directly.
    Python/SQLAlchemy stay snake_case (idiomatic on this side), but JSON
    over the wire is camelCase — matching the frontend's existing TS types
    (`recordedAt`, `fromAyah`, ...) exactly, so no field-renaming layer is
    needed on the client.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
