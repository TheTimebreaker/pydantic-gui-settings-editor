from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


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
    ratio: float = Field(0.5, ge=0.0, le=1.0)
    name: str = Field("test")
    option: TestEnum = Field(TestEnum.THIRD)
    options: set[TestEnum] = Field(set(TestEnum))
    nested: NestedSettings = Field(default_factory=NestedSettings)
