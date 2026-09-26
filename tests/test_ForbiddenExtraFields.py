import example_model  # noqa: N999
import pytest
from pydantic import ValidationError

bonus_field = "unknown_field_sahjsa"
payload = {"enabled": False, "count": 17, bonus_field: 42}


def test_extra_ignore() -> None:
    model_cls = example_model.model_with_extra_config("ignore")
    model = model_cls(**payload)  # type: ignore
    assert getattr(model, bonus_field, None) is None


def test_extra_allowed() -> None:
    model_cls = example_model.model_with_extra_config("allow")
    model = model_cls(**payload)  # type: ignore
    assert getattr(model, bonus_field, None) is not payload.get("bonus_field")


def test_extra_forbidden() -> None:
    model_cls = example_model.model_with_extra_config("forbid")
    with pytest.raises(ValidationError):
        model_cls(**payload)  # type: ignore
