from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from pydantic_gui_settings_editor.types import DirectoryPath, FilePath


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
    names: set[str] = Field({"test1", "test2"})
    option: TestEnum = Field(TestEnum.THIRD)
    options: set[TestEnum] = Field(set(TestEnum))
    nested: NestedSettings = Field(default_factory=NestedSettings)

    path: Path = Field(default=Path("."))
    filepath: FilePath = Field(default=Path("./README.md"))
    dirpath: DirectoryPath = Field(default=Path("./temp"))

    paths: set[Path] = Field(
        default={
            Path("./README.md"),
            Path("./HAHAHAHA"),
        }
    )
    filepaths: set[FilePath] = Field(
        default={
            Path("./README.md"),
            Path("./test.txt"),
        }
    )
    dirpaths: set[DirectoryPath] = Field(
        default={
            Path("./temp"),
            Path("./cheats"),
        }
    )


def model_with_extra_config(extra: Literal["allow", "forbid", "ignore"]) -> type[TestSettings]:
    model_cls = TestSettings
    model = create_model(
        f"{model_cls.__name__}_{extra}",
        __base__=model_cls,
        __config__=ConfigDict(extra=extra),
    )
    return model
