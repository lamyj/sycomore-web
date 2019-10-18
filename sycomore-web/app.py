# https://linuxfr.org/news/creer-une-application-web-avec-jupyter-ipywidgets-et-voila-7b03d5dd-ab10-47cb-a2bd-bd99fa9e2457
# Run `voila app.ipynb`

import ipywidgets

import fse
import rf_spoiling

tabs = [fse, rf_spoiling]

tab_widget = ipywidgets.widgets.Tab([x.tab for x in tabs], selected_index = 1)
for index, tab in enumerate(tabs):
    tab_widget.set_title(index, tab.name)

main = ipywidgets.VBox([
    ipywidgets.widgets.HTML(value="""<h1 style="text-align:center">MRI Simulation</h1>"""), tab_widget])
