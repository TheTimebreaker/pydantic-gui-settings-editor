from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model


class TestEnum(StrEnum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"


class NestedSettings(BaseModel):
    enabled: bool = True
    name: str = "nested"


class TestSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(True)
    count: int = Field(10, ge=0, le=100)
    ratio: float = Field(0.5, ge=0.0, le=100.0)
    name: str = Field("test", min_length=2, max_length=20)
    option: TestEnum = Field(TestEnum.THIRD)
    options: set[TestEnum] = Field(set(TestEnum))
    nested: NestedSettings = Field(default_factory=NestedSettings)


def model_with_extra_config(extra: Literal["allow", "forbid", "ignore"]) -> type[TestSettings]:
    model_cls = TestSettings
    model = create_model(
        f"{model_cls.__name__}_{extra}",
        __base__=model_cls,
        __config__=ConfigDict(extra=extra),
    )
    return model
