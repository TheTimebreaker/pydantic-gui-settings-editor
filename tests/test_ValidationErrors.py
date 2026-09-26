from typing import Any  # noqa: N999

import pytest
from pydantic import ValidationError


def test_validation_errors_bool(model_cls: type[Any]) -> None:
    model_cls(enabled=False)
    with pytest.raises(ValidationError):
        model_cls(enabled="hello")
    with pytest.raises(ValidationError):
        model_cls(enabled=15)
    with pytest.raises(ValidationError):
        model_cls(enabled=67.8)
    with pytest.raises(ValidationError):
        model_cls(enabled=bool)


def test_validation_errors_int(model_cls: type[Any]) -> None:
    model_cls(count=10)
    model_cls(count=98.0)
    with pytest.raises(ValidationError):
        model_cls(count=101)  # too big
    with pytest.raises(ValidationError):
        model_cls(count=-14)  # too small
    with pytest.raises(ValidationError):
        model_cls(count=10.0001)  # float
    with pytest.raises(ValidationError):
        model_cls(count=10.7)  # float
    with pytest.raises(ValidationError):
        model_cls(count="based")  # str


def test_validation_errors_float(model_cls: type[Any]) -> None:
    model_cls(ratio=10.1)
    model_cls(ratio=7 / 9)
    model_cls(ratio=10)
    model_cls(ratio=300 / 100)
    with pytest.raises(ValidationError):
        model_cls(ratio=101.97)  # too big
    with pytest.raises(ValidationError):
        model_cls(ratio=-14.44)  # too small
    with pytest.raises(ValidationError):
        model_cls(ratio="based")  # str


def test_validation_errors_str(model_cls: type[Any]) -> None:
    model_cls(name="17")
    model_cls(name="based")
    with pytest.raises(ValidationError):
        model_cls(name="0")  # too short
    with pytest.raises(ValidationError):
        model_cls(name="hajshjsd ashjhdsajds hasjd hsdajhdsa jahds jadshj hsdj hdsjsda")  # too long
    with pytest.raises(ValidationError):
        model_cls(name="                                              balloon")  # too long
    with pytest.raises(ValidationError):
        model_cls(name=10)
    with pytest.raises(ValidationError):
        model_cls(name=10.0)
    with pytest.raises(ValidationError):
        model_cls(name=10.01)
    with pytest.raises(ValidationError):
        model_cls(name=True)
