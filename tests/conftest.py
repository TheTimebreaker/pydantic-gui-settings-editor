import example_model
import pytest
from pydantic import BaseModel
from PySide6.QtWidgets import QApplication


@pytest.fixture(autouse=True)
def qt_app() -> QApplication:
    val = QApplication.instance() or QApplication([])
    assert isinstance(val, QApplication)
    return val


@pytest.fixture(
    params=(
        pytest.param("allow", id="extra-allow"),
        pytest.param("forbid", id="extra-forbid"),
        pytest.param("ignore", id="extra-ignore"),
    ),
)
def model_cls(request: pytest.FixtureRequest) -> type[BaseModel]:
    extra_mode = request.param
    return example_model.model_with_extra_config(extra_mode)
