from enum import Enum, StrEnum
from typing import Any, cast, get_args, get_origin

from annotated_types import Ge, Gt, Le, Lt, MaxLen, MultipleOf
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QMouseEvent, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pydantic_gui_settings_editor.config import ConfigCollapeNestedSettings, SettingsManagerConfig
from pydantic_gui_settings_editor.types import ModelT  # noqa: F401


class FieldKind(StrEnum):
    MODEL = "model"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    ENUM = "enum"
    SET_ENUM = "set_enum"
    UNKNOWN = "unknown"


class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()


class PersistentMenu(QMenu):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._pressed_action: QAction | None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        action = self.actionAt(event.position().toPoint())

        if action is not None and action.isCheckable():
            self._pressed_action = action
            event.accept()
            return

        self._pressed_action = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        action = self.actionAt(event.position().toPoint())

        if action is not None and action is self._pressed_action and action.isCheckable():
            action.setChecked(not action.isChecked())
            self._pressed_action = None
            event.accept()
            return

        self._pressed_action = None
        super().mouseReleaseEvent(event)


class EnumSetWidget(QPushButton):
    def __init__(
        self,
        enum_type: type[Enum],
        value: set[Enum],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.enum_type = enum_type
        self._value = set(value)

        self.setText(self._button_text())

        self.menu: PersistentMenu = PersistentMenu(self)  # type: ignore

        for option in sorted(enum_type, key=self.enum_sort_key):
            title = getattr(option, "title", None)  # Devs SHOULD overwrite the title property of Enums, but they also should not HAVE to do that
            if callable(title):
                title = title()
            if title is None:
                title = option.name
            action = self.menu.addAction(title)
            action.setCheckable(True)
            action.setChecked(option in self._value)
            action.toggled.connect(
                lambda checked, option=option: self._set_option(
                    option,
                    checked,
                )
            )

        self.setMenu(self.menu)

    def enum_sort_key(self, option: Enum) -> str | int:
        result = getattr(option, "sort_key", option.value)
        if isinstance(result, int) or isinstance(result, str):
            return result
        raise ValueError(f"The sort key is not a supported type. This is almost certainly a bug. The actual type was {type(result)}")

    def _set_option(
        self,
        option: Enum,
        checked: bool,
    ) -> None:
        if checked:
            self._value.add(option)
        else:
            self._value.discard(option)

        self.setText(self._button_text())

    def _button_text(self) -> str:
        count = len(self._value)

        if count == 0:
            return "None selected"

        if count == len(self.enum_type):
            return "All selected"

        return f"{count} selected"

    def value(self) -> set[Enum]:
        return set(self._value)

    def setValue(self, value: set[Enum]) -> None:  # noqa: N802
        self._value = set(value)

        for action in self.menu.actions():
            option = action.data()
            action.setChecked(option in self._value)

        self.setText(self._button_text())


def classify_field(field: FieldInfo) -> FieldKind:
    annotation = field.annotation

    # Nested Pydantic model
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return FieldKind.MODEL

    # Simple scalar types
    if annotation is bool:
        return FieldKind.BOOL
    elif annotation is int:
        return FieldKind.INT
    elif annotation is float:
        return FieldKind.FLOAT
    elif annotation is str:
        return FieldKind.STR

    # Direct enum
    elif isinstance(annotation, type) and issubclass(annotation, Enum):
        return FieldKind.ENUM

    # Generic/container types
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is set and len(args) == 1:
        element_type = args[0]
        if isinstance(element_type, type) and issubclass(element_type, Enum):
            return FieldKind.SET_ENUM

    return FieldKind.UNKNOWN


def create_widget(field: FieldInfo, value: Any) -> QWidget:
    def as_int(value: object) -> int:
        return int(cast(int | float, value))

    def as_float(value: object) -> float:
        return float(cast(int | float, value))

    kind = classify_field(field)
    widget: QWidget
    min_value: int | float | None
    max_value: int | float | None
    step: int | float | None

    if kind is FieldKind.BOOL:
        widget = QCheckBox()
        widget.setChecked(value)
        widget.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Fixed,
        )
        return widget

    elif kind is FieldKind.INT:
        widget = NoWheelSpinBox()

        min_value = None
        max_value = None
        step = None
        for item in field.metadata:
            if isinstance(item, Ge):
                min_value = as_int(item.ge)
            elif isinstance(item, Gt):
                min_value = as_int(item.gt) + 1
            elif isinstance(item, Le):
                max_value = as_int(item.le)
            elif isinstance(item, Lt):
                max_value = as_int(item.lt) - 1
            elif isinstance(item, MultipleOf):
                step = as_int(item.multiple_of)
        if min_value is not None:
            widget.setMinimum(min_value)
        if max_value is not None:
            widget.setMaximum(max_value)
        if step is not None:
            widget.setSingleStep(step)

        widget.setValue(value)
        return widget

    elif kind is FieldKind.FLOAT:
        widget = NoWheelDoubleSpinBox()

        min_value = None
        max_value = None
        step = None
        for item in field.metadata:
            if isinstance(item, Ge):
                min_value = as_float(item.ge)
            elif isinstance(item, Gt):
                min_value = as_float(item.gt) + 1
            elif isinstance(item, Le):
                max_value = as_float(item.le)
            elif isinstance(item, Lt):
                max_value = as_float(item.lt) - 1
            elif isinstance(item, MultipleOf):
                step = as_float(item.multiple_of)
        if min_value is not None:
            widget.setMinimum(min_value)
        if max_value is not None:
            widget.setMaximum(max_value)
        if step is not None:
            widget.setSingleStep(step)

        widget.setValue(value)
        return widget

    elif kind is FieldKind.STR:
        widget = QLineEdit()

        max_value = None
        for item in field.metadata:
            if isinstance(item, MaxLen):
                max_value = item.max_length
        if max_value is not None:
            widget.setMaxLength(max_value)

        widget.setText(value)
        return widget

    elif kind is FieldKind.ENUM:
        widget = NoWheelComboBox()
        widget.setFocusPolicy(Qt.FocusPolicy.TabFocus)

        enum_type = field.annotation
        if enum_type is None or not issubclass(enum_type, Enum):
            raise TypeError(f"Expected an enum annotation, got {enum_type!r}")

        for option in enum_type:
            title = getattr(option, "title", None)
            if callable(title):  # Devs SHOULD overwrite the title property of Enums, but they also should not HAVE to do that
                title = title()
            if title is None:
                title = option.name
            widget.addItem(
                title,
                userData=option,
            )

        index = widget.findData(value)
        if index == -1:
            raise ValueError(f"Enum value {value!r} was not found in {enum_type!r}")
        widget.setCurrentIndex(index)

        return widget

    elif kind is FieldKind.SET_ENUM:
        enum_type = get_args(field.annotation)[0]
        return EnumSetWidget(enum_type, value)

    raise TypeError(f"Don't know how to create a widget for {field.annotation!r}")


def get_widget_value(widget: QWidget) -> object:
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QSpinBox):
        return widget.value()
    if isinstance(widget, QDoubleSpinBox):
        return widget.value()
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentData()
    if isinstance(widget, EnumSetWidget):
        return widget.value()

    raise TypeError(f"Unsupported widget: {type(widget).__name__}")


class ClickableLabel(QLabel):
    def __init__(
        self,
        text: str,
        target: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.target = target

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self.target.setFocus()
        QTest.mouseClick(
            self.target,
            event.button(),
        )
        super().mousePressEvent(event)


class CollapsibleGroupBox(QGroupBox):
    def __init__(
        self,
        title: str,
        content: QWidget,
        start_expanded: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._header = QToolButton()
        self._header.setText(title)
        self._header.setCheckable(True)
        self._header.setChecked(start_expanded)
        self._header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._header.setArrowType(Qt.ArrowType.DownArrow if start_expanded else Qt.ArrowType.RightArrow)
        self._header.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self._header.clicked.connect(self._toggle)

        # this is necessary to fix the INSANELY ugly default coloring of this element
        self._header.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                padding: 4px;
                text-align: left;
            }
            QToolButton:checked {
                border: none;
                background: transparent;
            }
            QToolButton:hover {
                background: transparent;
            }
            """)

        self._content = content
        if not start_expanded:
            self._content.setVisible(start_expanded)

        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addWidget(self._content)

    def _toggle(self, expanded: bool) -> None:
        self._content.setVisible(expanded)
        self._header.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow,
        )

    def set_description(self, description: str) -> None:
        self._header.setToolTip(description)


class SettingsForm[ModelT: BaseModel](QWidget):
    def __init__(self, model: ModelT, parent: QGroupBox | None = None, additional_config: SettingsManagerConfig | None = None) -> None:
        super().__init__(parent)
        self.model_type: type[ModelT] = type(model)
        if additional_config is None:
            additional_config = SettingsManagerConfig()
        self.additional_config = additional_config

        self.widgets: dict[str, QWidget] = {}
        self.child_forms: dict[str, SettingsForm[ModelT]] = {}
        layout = QFormLayout(self)
        start_expanded = self.additional_config.collapsed_nested_settings == ConfigCollapeNestedSettings.ENABLED_EXPANDED

        for name, field in self.model_type.model_fields.items():
            value = getattr(model, name)
            kind = classify_field(field)
            description = field.description if self.additional_config.enable_tooltips else None

            if kind is FieldKind.MODEL:
                child_form = SettingsForm(value, additional_config=self.additional_config)
                self.child_forms[name] = child_form

                if self.additional_config.collapsed_nested_settings == ConfigCollapeNestedSettings.DISABLED:
                    group = QGroupBox(field.title or name)
                    if description:
                        group.setToolTip(description)
                    group_layout = QFormLayout(group)
                    group_layout.addRow(child_form)
                else:
                    group = CollapsibleGroupBox(field.title or name, child_form, start_expanded=start_expanded)
                    if description:
                        group.set_description(description)
                layout.addRow(group)

            else:
                widget = create_widget(field, value)
                label = ClickableLabel(field.title or name, target=widget)

                if description:
                    label.setToolTip(description)
                    widget.setToolTip(description)

                layout.addRow(label, widget)
                self.widgets[name] = widget

    def get_values(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for name, widget in self.widgets.items():
            values[name] = get_widget_value(widget)
        for name, form in self.child_forms.items():
            values[name] = form.get_values()
        return values

    def get_model(self) -> ModelT:
        try:
            return self.model_type.model_validate(self.get_values())
        except ValidationError as e:
            errors = "\n".join(f"• {err['loc']}: {err['msg']}" for err in e.errors())
            QMessageBox.critical(
                self,
                "Invalid input",
                f"Some of your input is invalid. Please fix the following errors, otherwise you cannot save your changes:\n\n{errors}",
            )
            raise

    def set_model(self, model: ModelT) -> None:
        self.model_type = type(model)
        for name, widget in self.widgets.items():
            value = getattr(model, name)
            if isinstance(widget, QCheckBox):
                widget.setChecked(value)
            elif isinstance(widget, QSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QLineEdit):
                widget.setText(value)
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(widget.findData(value))
            elif isinstance(widget, EnumSetWidget):
                widget.setValue(value)
            else:
                raise TypeError(f"Unsupported widget: {type(widget).__name__}")

        for name, form in self.child_forms.items():
            form.set_model(getattr(model, name))
