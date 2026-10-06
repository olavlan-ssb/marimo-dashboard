# /// script
# dependencies = [
#   "anywidget",
#   "traitlets",
# ]
# ///

import pathlib

import anywidget
import traitlets

_JS_PATH = pathlib.Path(__file__).parent / "widgets"
_CSS_FILE = pathlib.Path(__file__).parent / "designsystemet/index.css"


class Dropdown(anywidget.AnyWidget):
    _esm = _JS_PATH / "dropdown.js"
    _css = _CSS_FILE

    options = traitlets.List(trait=traitlets.Unicode(), default_value=[]).tag(sync=True)
    selected = traitlets.Unicode().tag(sync=True)


class Form(anywidget.AnyWidget):
    _esm = _JS_PATH / "form.js"
    _css = _CSS_FILE

    form_data = traitlets.Dict(default_value={}).tag(sync=True)
    submitted = traitlets.Bool(False).tag(sync=True)
