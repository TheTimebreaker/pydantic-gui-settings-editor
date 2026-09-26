import os  # noqa: N999
import tempfile
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import pytest

from pydantic_gui_settings_editor.manager import SettingsManager


def test_save_and_load(model_cls: type[Any]) -> None:
    file_descriptor, ospath = tempfile.mkstemp(suffix=".json", prefix="settings", text=True)
    os.close(file_descriptor)
    settings_path = Path(ospath)
    try:
        manager = SettingsManager(
            model_cls,
            settings_path,
        )
        manager.model = model_cls(
            enabled=False,
            count=42,
        )
        manager.edit_gui(auto_confirm_gui=True)
        manager.save()

        other_manager = SettingsManager(
            model_cls,
            settings_path,
        )
        other_manager.load()

        assert other_manager.model == manager.model

    finally:
        settings_path.unlink(missing_ok=True)


def test_load_missing_file_uses_defaults(model_cls: type[Any]) -> None:
    file_descriptor, ospath = tempfile.mkstemp(suffix=".json", prefix="missing", text=True)
    os.close(file_descriptor)
    missingfield_path = Path(ospath)
    try:
        missingfield_path.write_text(data="{}")
        manager = SettingsManager(
            model_cls,
            missingfield_path,
        )
        manager.load()
        assert manager.model == model_cls()

    finally:
        missingfield_path.unlink(missing_ok=True)


def test_invalid_json(model_cls: type[Any]) -> None:
    file_descriptor, ospath = tempfile.mkstemp(suffix=".json", prefix="missing", text=True)
    os.close(file_descriptor)
    missingfield_path = Path(ospath)
    try:
        missingfield_path.write_text(data="{ invalid json")
        manager = SettingsManager(
            model_cls,
            missingfield_path,
        )
        with pytest.raises(JSONDecodeError):
            manager.load()

    finally:
        missingfield_path.unlink(missing_ok=True)


@pytest.fixture(params=("allow", "ignore"))
def test_load_warns_about_unknown_fields(
    model_cls: type[Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    file_descriptor, ospath = tempfile.mkstemp(suffix=".json", prefix="missing", text=True)
    os.close(file_descriptor)
    settings_path = Path(ospath)
    try:
        settings_path.write_text(
            '{"enabled": true, "not_in_pydantic_adsfjhdsfjhhdfsjhfhdsujhdfsuhfdesuhfds": 123}',
            encoding="utf-8",
        )
        manager = SettingsManager(
            model_cls,
            settings_path,
        )
        manager.load()
        assert "old_setting" in caplog.text

    finally:
        settings_path.unlink(missing_ok=True)
