import json
import logging
import shutil
from pathlib import Path

from pydantic import BaseModel
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pydantic_gui_settings_editor.config import SettingsManagerConfig, Theme
from pydantic_gui_settings_editor.gui import SettingsForm
from pydantic_gui_settings_editor.types import ModelT  # noqa: F401


def give_backup_path(path: Path) -> Path:
    return path.with_name(path.name + ".bak")


class SettingsManager[ModelT: BaseModel]:
    """This class manages a Pydantic settings model, included loading from disk, editing via GUI and saving to disk.

    The pydantic model remains the single source of truth, while the PySide6 GUI is used to edit the model.

    Args:
        model_type: The Pydantic model class used for the settings.
        settings_path: Path to the JSON settings file.
        additional_config: An instance of SettingsManagerConfig, that is used by the developer (not the user) to configure how
        the SettingsManager behaves and is styled.
    """

    def __init__(self, model_type: type[ModelT], settings_path: Path, additional_config: SettingsManagerConfig | None = None) -> None:
        logging.debug("Initializing SettingsManager.")
        self.model_type = model_type
        self.settings_path = settings_path

        if additional_config is None:
            additional_config = SettingsManagerConfig()
        self.additional_config = additional_config
        self.create_backup: bool = self.additional_config.create_backup
        self.encoding = self.additional_config.encoding

        self.model: ModelT
        self.saved_model: ModelT
        self.used_disk_file: bool
        self._form: SettingsForm[ModelT]
        self.app: QApplication
        self.window: QMainWindow

        self._init_qt()

        logging.debug("SettingsManager initialized.")

    @property
    def _is_modified(self) -> bool:
        return not self.used_disk_file or self.model != self.saved_model

    def load(self) -> None:
        """Loads settings from disk, or uses the model defaults if no file exists.

        Unknown fields in the settings file are logged as warnings. Validation
        is still performed by Pydantic, so model-specific validation rules are
        respected."""

        def load_model_from_file(file_path: Path) -> ModelT:
            raw_data = file_path.read_text(encoding=self.encoding)
            data = json.loads(raw_data)
            if isinstance(data, dict):
                extra_fields = set(data) - set(self.model_type.model_fields)
                if extra_fields:
                    logging.warning(
                        "Settings file contains unknown fields: %s",
                        ", ".join(sorted(extra_fields)),
                    )
            return self.model_type.model_validate_json(raw_data)

        try:
            if not self.settings_path.is_file():
                raise FileNotFoundError
            self.model = load_model_from_file(self.settings_path)
            self.used_disk_file = True
            logging.info("Loaded settings from disk.")

        except FileNotFoundError:
            self.model = self.model_type()
            self.used_disk_file = False
            logging.info("No settings file was found; using defaults.")

        except (UnicodeDecodeError, PermissionError) as error:
            logging.error(
                "Unable to read the settings file at %s due to a %s. Asking whether to load the backup file.",
                self.settings_path,
                error.__class__.__name__,
            )
            use_backup_file = QMessageBox.question(
                None,
                "Can't read settings file",
                f"An {error.__class__.__name__} prevented reading the settings file. Do you want to try loading the backup file? "
                "Keep in mind that this may cause your last changes to the config to be overwritten.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if use_backup_file == QMessageBox.StandardButton.No:
                raise

            backup_path = give_backup_path(self.settings_path)
            if not backup_path.is_file():
                raise FileNotFoundError(
                    "The main settings file at %s is unreadable, and the backup file does not exist. "
                    "Please check the file yourself; if it truly appears unrecoverable, delete it or move it elsewhere.",
                    self.settings_path,
                ) from error
            self.model = load_model_from_file(backup_path)
            self.used_disk_file = True
            logging.info("Loaded settings from disk (backup).")

        except json.JSONDecodeError as error:
            logging.error(
                "Unable to read the settings file at %s due to a %s. "
                "This should not happen unless the file was manually edited or is otherwise malformed. "
                "Please check the error message, which should indicate where and how the file is malformed.",
                self.settings_path,
                error.__class__.__name__,
            )
            raise error

        self.saved_model = self.model.model_copy(deep=True)

    def _init_qt(self) -> None:
        self.app = QApplication([])
        self.window = QMainWindow()

        self.window.setWindowTitle(self.additional_config.title)

        icon_path = self.additional_config.icon_path
        if icon_path is not None:
            if not icon_path.is_file():
                raise FileNotFoundError(f"Icon file does not exist: {icon_path}")
            icon = QIcon(str(icon_path))
            self.app.setWindowIcon(icon)
            self.window.setWindowIcon(icon)

        theme = self.additional_config.theme
        if theme is Theme.LIGHT:
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Light)
        elif theme is Theme.DARK:
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)

    def edit_gui(self) -> None:
        """Opens the graphical settings editor.

        The GUI can edit a copy of the current settings. Changes are only written to disk when saved."""
        logging.info("Opening the settings editor...")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        working_copy = self.model.model_copy(deep=True)
        self._form = SettingsForm(working_copy, additional_config=self.additional_config)
        scroll.setWidget(self._form)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(scroll)
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        save_exit_button = QPushButton("Save && Exit")
        save_exit_button.clicked.connect(self._save_and_exit)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self._exit)
        defaults_button = QPushButton("Set all to defaults")
        defaults_button.clicked.connect(self._reset_to_default)
        undo_button = QPushButton("Undo changes")
        undo_button.clicked.connect(self._undo_changes)

        button_layout.addWidget(save_button)
        button_layout.addWidget(save_exit_button)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(defaults_button)
        button_layout.addWidget(undo_button)

        main_layout.addLayout(button_layout)

        self.window.setCentralWidget(central_widget)
        self.window.resize(800, 600)
        self.window.show()
        self.app.exec()

        self.model = self._form.get_model()

    def save(self) -> None:
        """Save current model state to disk and set the fallback state to the current state.

        (the fallback state gets used when options like "Undo changes" are used)
        """
        logging.info("Saving model to disk...")
        self.model = self._form.get_model()
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        if self._is_modified is False:
            logging.info("Not saved because no changes were made...")
            return

        if self.create_backup is True and self.settings_path.is_file():
            logging.info("Creating model file backup...")
            backup_path = give_backup_path(self.settings_path)
            shutil.copy2(self.settings_path, backup_path)

        self.settings_path.write_text(
            self.model.model_dump_json(indent=4),
            encoding=self.encoding,
        )
        self.saved_model = self.model.model_copy(deep=True)
        self.used_disk_file = True
        logging.info("Saving model to disk... Done!")

    def _exit(self) -> None:
        """Exits the editing GUI, prompting about unsaved changes if necessary."""
        self.model = self._form.get_model()

        if not self._is_modified:
            self._form.window().close()
            return

        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Warning)
        message_box.setWindowTitle("Unsaved changes")
        message_box.setText("There are unsaved changes.")
        message_box.setInformativeText("Do you want to save your changes before exiting?")

        save_button = message_box.addButton(
            "Save changes",
            QMessageBox.ButtonRole.AcceptRole,
        )
        discard_button = message_box.addButton(
            "Discard changes",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel_button = message_box.addButton(
            "Cancel",
            QMessageBox.ButtonRole.RejectRole,
        )
        message_box.exec()

        clicked_button = message_box.clickedButton()
        if clicked_button is save_button:
            self.save()
            self._form.window().close()
        elif clicked_button is discard_button:
            self._form.window().close()
        elif clicked_button is cancel_button:
            return

    def _save_and_exit(self) -> None:
        self.save()
        self._exit()

    def _reset_to_default(self) -> None:
        """Resets the internally stored model instance to the default model state (all values set to default).
        THIS WILL OVERWRITE YOUR CHANGES, IF YOU SAVE THIS."""
        logging.info("Resetting model to default state.")
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Warning)
        message_box.setWindowTitle("Overwriting current settings")
        message_box.setText(
            "This will overwrite your current settings and reset all values to their defaults. If you save afterwards, the changes will be kept."
        )
        message_box.setInformativeText("Do you want to continue with this action?")

        overwrite = message_box.addButton(
            "Overwrite with default",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel_button = message_box.addButton(
            "Cancel",
            QMessageBox.ButtonRole.RejectRole,
        )
        cancel_button.setDefault(True)
        message_box.exec()
        clicked_button = message_box.clickedButton()

        if clicked_button is overwrite:
            self.model = self.model_type()
            working_copy = self.model.model_copy(deep=True)
            self._form.set_model(working_copy)
        elif clicked_button is cancel_button:
            return

    def _undo_changes(self) -> None:
        """Undo all changes done to the internal model state since last saving."""
        logging.info("Undoing changes made since last save.")
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Warning)
        message_box.setWindowTitle("Undo last changes")
        message_box.setText("This will undo every change made since your last save. If you save afterwards, the changes will be kept.")
        message_box.setInformativeText("Do you want to continue with this action?")
        undo_changes = message_box.addButton(
            "Undo changes",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel_button = message_box.addButton(
            "Cancel",
            QMessageBox.ButtonRole.RejectRole,
        )
        cancel_button.setDefault(True)
        message_box.exec()
        clicked_button = message_box.clickedButton()

        if clicked_button is undo_changes:
            self.model = self.saved_model.model_copy(deep=True)
            working_copy = self.model.model_copy(deep=True)
            self._form.set_model(working_copy)
        elif clicked_button is cancel_button:
            return
