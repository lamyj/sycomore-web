import pathlib

import bokeh.models

here = pathlib.Path(__file__).parent

title = "Home"

def create_contents():
    return bokeh.models.Div(text=(here/"home.html").read_text())

def init():
    pass
