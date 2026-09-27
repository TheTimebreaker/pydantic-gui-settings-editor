import platformdirs

import pydantic_gui_settings_editor
from tests.example_model import TestSettings

try:
    config_path = platformdirs.PlatformDirs("Pydantic GUI Settings editor", "TheTimebreaker").user_config_path / "development-testing-config.json"
    settings = TestSettings()  # type: ignore

    manager_settings = pydantic_gui_settings_editor.SettingsManagerConfig()
    manager = pydantic_gui_settings_editor.SettingsManager(TestSettings, config_path, manager_settings)
    manager.load()
    manager.edit_gui()

finally:
    print("=" * 20)
    print("When finished with developing, don't forget to wipe your devving config file!")
    print("It can be found here:")
    print(config_path)
