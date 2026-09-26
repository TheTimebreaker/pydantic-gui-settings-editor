from typing import Any  # noqa: N999

import example_model  # type: ignore

from pydantic_gui_settings_editor.config import SettingsManagerConfig
from pydantic_gui_settings_editor.gui import SettingsForm


def test_model_round_trip(model_cls: type[Any]) -> None:
    original = model_cls(
        enabled=False,
        count=42,
        ratio=0.75,
        name="hellooooo",
        option=example_model.TestEnum.SECOND,
        options=set([example_model.TestEnum.FIRST, example_model.TestEnum.THIRD]),
        nested=example_model.NestedSettings(
            enabled=False,
            name="child",
        ),
    )
    form = SettingsForm(original)
    result = form.get_model()
    assert result == original


def test_model_round_trip2(model_cls: type[Any]) -> None:
    original = model_cls(
        enabled=True,
        count=69,
        ratio=0.6777777,
        name="  balloon  ",
        option=example_model.TestEnum.THIRD,
        options=set([example_model.TestEnum.SECOND, example_model.TestEnum.FIRST]),
        nested=example_model.NestedSettings(
            enabled=True,
            name="  hahahaha  ",
        ),
    )
    form = SettingsForm(original)
    result = form.get_model()
    assert result == original


def test_float_precision(model_cls: type[Any]) -> None:
    model = model_cls(ratio=0.6778)
    conf = SettingsManagerConfig(float_precision=4)
    form = SettingsForm(model, additional_config=conf)
    assert form.get_model().ratio == model.ratio


def test_float_precision2(model_cls: type[Any]) -> None:
    model = model_cls(ratio=0.67745648574651)
    conf = SettingsManagerConfig(float_precision=15)
    form = SettingsForm(model, additional_config=conf)
    assert form.get_model().ratio == model.ratio


def test_float_precision3(model_cls: type[Any]) -> None:
    model = model_cls(ratio=0.67745648574651)
    conf = SettingsManagerConfig(float_precision=14)
    form = SettingsForm(model, additional_config=conf)
    assert form.get_model().ratio == model.ratio


def test_failing_float(model_cls: type[Any]) -> None:
    inp_float = 0.67745648574651
    float_precision = 12
    model = model_cls(ratio=inp_float)
    conf = SettingsManagerConfig(float_precision=float_precision)
    form = SettingsForm(model, additional_config=conf)
    assert form.get_model().ratio != model.ratio
    assert form.get_model().ratio == round(model.ratio, float_precision)


def test_set_model(model_cls: type[Any]) -> None:
    original = model_cls()
    replacement = model_cls(
        enabled=False,
        count=99,
        name="replacement",
        option=example_model.TestEnum.THIRD,
        options={example_model.TestEnum.SECOND},
        nested=example_model.NestedSettings(
            enabled=False,
            name="changed",
        ),
    )
    form = SettingsForm(original)
    form.set_model(replacement)
    get_model = form.get_model()
    assert get_model == replacement


def test_set_model2(model_cls: type[Any]) -> None:
    original = model_cls()
    replacement = model_cls(
        enabled=False,
        ratio=0.6666666667777,
        name="replacement",
        option=example_model.TestEnum.THIRD,
        options={example_model.TestEnum.THIRD, example_model.TestEnum.SECOND, example_model.TestEnum.FIRST},
        nested=example_model.NestedSettings(
            enabled=False,
            name=" c h a n g e d ",
        ),
    )
    form = SettingsForm(original)
    form.set_model(replacement)
    get_model = form.get_model()
    assert get_model == replacement


def test_nested_model_round_trip(model_cls: type[Any]) -> None:
    model = model_cls(
        nested=example_model.NestedSettings(
            enabled=False,
            name="nested value",
        ),
    )
    form = SettingsForm(model)
    assert form.get_model().nested == model.nested
