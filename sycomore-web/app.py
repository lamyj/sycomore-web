import pathlib

import ipywidgets

import fse
import rf_spoiling
import slice_profile

tabs = [rf_spoiling, slice_profile]

initialized_tabs = set()
def on_tab_selected(change):
    tabs[change["new"]].init()

here = pathlib.Path(__file__).parent
style = ipywidgets.widgets.HTML(
    f"""<style>{(here/"style.css").read_text()}</style>""")

tab_widget = ipywidgets.widgets.Tab([x.tab for x in tabs])
for index, tab in enumerate(tabs):
    tab_widget.set_title(index, tab.name)
tab_widget.observe(on_tab_selected, names="selected_index")
main = ipywidgets.VBox([
    ipywidgets.widgets.HTML(
        """<h1 class="main">Interactive MRI Simulations</h1>"""), 
    tab_widget])
tab_widget.selected_index = 0
