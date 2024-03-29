import collections

import bokeh.models
import bokeh.plotting

import home
import rare
import rf_spoiling_evolution
import rf_spoiling_efficiency
import se_contrast
import slice_profile

experiments = collections.OrderedDict(
    (x.__name__, x) 
    for x in [
        home, 
        rare, 
        rf_spoiling_evolution, rf_spoiling_efficiency, 
        se_contrast,
        slice_profile])

arguments = bokeh.plotting.curdoc().session_context.request.arguments
experiment = arguments.get("e", [b"home"])[0].decode()

if experiment in experiments:
    contents = experiments[experiment].create_contents()
    title = experiments[experiment].title
else:
    experiment = None
    contents = bokeh.models.Div(text="<h1>Unknown experiment</h1>")
    title = "Error"

contents.sizing_mode = "scale_both"

bokeh.plotting.curdoc().add_root(contents)
bokeh.plotting.curdoc().template_variables["experiments"] = experiments
bokeh.plotting.curdoc().title = title

if experiment is not None:
    experiments[experiment].init()
