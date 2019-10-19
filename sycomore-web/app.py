import ipywidgets

import fse
import rf_spoiling
import slice_profile

tabs = [rf_spoiling, slice_profile]

initialized_tabs = set()
def on_tab_selected(change):
    if change["new"] not in initialized_tabs:
        tabs[change["new"]].update_plot(None)
        initialized_tabs.add(change["new"])

tab_widget = ipywidgets.widgets.Tab([x.tab for x in tabs], selected_index=0)
for index, tab in enumerate(tabs):
    tab_widget.set_title(index, tab.name)
tab_widget.observe(on_tab_selected, names="selected_index")
main = ipywidgets.VBox([
    ipywidgets.widgets.HTML(value="""<h1 style="text-align:center">MRI Simulation</h1>"""), 
    tab_widget])
on_tab_selected({"new": 0})
