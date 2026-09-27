from pathlib import Path
from typing import Annotated, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class _FilePathMarker:
    pass


class _DirectoryPathMarker:
    pass


FilePath = Annotated[Path, _FilePathMarker]
"""Path marker that marks a Path to a file."""

DirectoryPath = Annotated[Path, _DirectoryPathMarker]
"""Path marker that marks a Path to a directory."""
