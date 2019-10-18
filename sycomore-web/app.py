import ipywidgets

import fse
import rf_spoiling
import slice_profile

tabs = [rf_spoiling, slice_profile]

tab_widget = ipywidgets.widgets.Tab([x.tab for x in tabs], selected_index=0)
for index, tab in enumerate(tabs):
    tab_widget.set_title(index, tab.name)

main = ipywidgets.VBox([
    ipywidgets.widgets.HTML(value="""<h1 style="text-align:center">MRI Simulation</h1>"""), tab_widget])
