from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(
    Path(__file__).parent.parent.parent / "tools" / "lead_qualifier" / "assistant_app.py"
)


def test_assistant_page_loads_without_calling_external_apis():
    app = AppTest.from_file(APP_PATH)
    app.run()

    assert not app.exception
    assert app.chat_input
    assert app.chat_input[0].placeholder == "Ask Family Secret… | Спросите о ресторане…"

