from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


class Theme(StrEnum):
    """This enum lets you define a theme for the application."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class Encoding(StrEnum):
    """This enum lets you choose the encoding used for the on-disk settings file."""

    UTF8 = "utf-8"
    UTF16 = "utf-16"
    ASCII = "ascii"


class ConfigCollapeNestedSettings(StrEnum):
    DISABLED = "disabled"
    """Disables collapsing nested settings entirely."""
    ENABLED_COLLAPSED = "start collapsed"
    """Enables collapsing nested settings and starts all nested sections collapsed."""
    ENABLED_EXPANDED = "start expanded"
    """Enables collapsing nested settings and starts all nested sections expanded."""


class SettingsManagerConfig(BaseModel):
    """This class configures a SettingsManager instance."""

    title: str = "Settings Editor"
    """Title displayed in the settings window."""

    theme: Theme = Theme.SYSTEM
    """Color scheme used by the application."""

    collapsed_nested_settings: ConfigCollapeNestedSettings = ConfigCollapeNestedSettings.ENABLED_EXPANDED
    """Controls nested settings to be collapsable."""

    create_backup: bool = True
    """Flag that forces a backup file to be created before changes are written to disk."""

    enable_tooltips: bool = True
    """Flag that will show the description of a field as a tooltip, when hovering over it in the GUI."""

    encoding: Encoding = Encoding.UTF8
    """Encoding used for the stored settings files."""

    icon_path: Path | None = None
    """Path to the image file used for the settings window icon and the taskbar icon."""
