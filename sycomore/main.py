import bokeh.layouts
import bokeh.models
import bokeh.plotting

import fse
import home
import rf_spoiling_evolution
import rf_spoiling_efficiency
import slice_profile

experiments = {
    x.__name__: x for x in [
        home, 
        fse, 
        rf_spoiling_evolution, rf_spoiling_efficiency, 
        slice_profile]}

arguments = bokeh.plotting.curdoc().session_context.request.arguments
experiment = arguments.get("e", [b"home"])[0].decode()

header = bokeh.models.Div(
    text=
        """<h1 class="main">Sycomore</h1>"""
        +"""<ul class="menu">"""
        +"".join(f"""<li><a href="?e={k}">{v.title}</a></li>""" for k,v in experiments.items())
        +"</ul>")

if experiment in experiments:
    contents = experiments[experiment].create_contents()
    title = experiments[experiment].title
else:
    contents = bokeh.models.Div(text="<h1>Unknown experiment</h1>")
    title = "Error"

layout = bokeh.layouts.layout(
    [
        [header],
        [contents]
    ], 
    sizing_mode="scale_both")

bokeh.plotting.curdoc().add_root(layout)
bokeh.plotting.curdoc().title = title

experiments[experiment].init()
