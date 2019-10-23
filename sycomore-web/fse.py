import time

import bqplot.pyplot
import ipywidgets
import numpy
import sycomore
from sycomore.units import *

import utils

name = "Fast Spin Echo"

common_attributes = {
    "continuous_update": False, "style": {"description_width": "initial"}}
widgets = {
    "species": {
        "label": ipywidgets.widgets.HTML(value="""<h1 class="group">Species</h1>"""),
        "T1": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=600, step=1, description="T<sub>1</sub> (ms)",
            **common_attributes),
        "T2": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=400, step=1, description="T<sub>2</sub> (ms)",
            **common_attributes),
    },
    "sequence": {
        "label": ipywidgets.widgets.HTML(value="""<h1 class="group">Sequence</h1>"""),
        "excitation": ipywidgets.widgets.IntSlider(
            min=0, max=90, value=90, step=1, description="Excitation (°)",
            **common_attributes),
        "TE": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=200, step=1, description="TE (ms)",
            **common_attributes),
        "refocalization": ipywidgets.widgets.IntSlider(
            min=0, max=180, value=180, step=1, description="Refocalization (°)",
            **common_attributes),
        "TR": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=1000, step=1, description="TR (ms)",
            **common_attributes),
        "train_length": ipywidgets.widgets.BoundedIntText(
            min=1, max=10, value=3, step=1, description="Echo train length",
            **common_attributes),
        "repetitions": ipywidgets.widgets.BoundedIntText(
            min=1, max=10, value=4, step=1, description="Repetitions",
            **common_attributes)
    },
    "runtime": {"label": ipywidgets.widgets.Label()}
}

fig_layout = ipywidgets.widgets.Layout(width="750px", height="250px")

magnitude_figure = bqplot.pyplot.figure(
    fig_margin={"top": 0, "bottom": 0, "left": 70, "right": 20},
    layout=fig_layout)
magnitude_plot = bqplot.pyplot.plot([], [])
# bqplot.pyplot.xlabel("Time (s)")
bqplot.pyplot.ylabel("Magnitude")

phase_figure = bqplot.pyplot.figure(
    fig_margin={"top": 0, "bottom": 60, "left": 70, "right": 20},
    layout=fig_layout)
phase_plot = bqplot.pyplot.plot([], [])
bqplot.pyplot.xlabel("Time (s)")
bqplot.pyplot.ylabel("Phase (rad)")

def update_plot(change):
    start = time.time()
    
    species = sycomore.Species(
        widgets["species"]["T1"].value*ms, widgets["species"]["T2"].value*ms)
    
    m0 = [0., 0., 1., 1.]
    
    TR = widgets["sequence"]["TR"].value*ms
    TE = widgets["sequence"]["TE"].value*ms
    
    time_step = 10*ms
    train_length = widgets["sequence"]["train_length"].value
    repetitions = widgets["sequence"]["repetitions"].value
    
    voxel_size = 1*mm
    positions_count = 50
    
    steps = 1+int((repetitions*TR/time_step).magnitude)
    times = [x.convert_to(s) for x in sycomore.linspace(0*s, repetitions*TR, steps)]

    excitation = sycomore.bloch.pulse(
        widgets["sequence"]["excitation"].value*deg, 90*deg)
    refocalization = sycomore.bloch.pulse(
        widgets["sequence"]["refocalization"].value*deg, 0*rad)
        
    positions = sycomore.linspace(voxel_size, positions_count)
    gradient = (
        2*numpy.pi*rad/sycomore.gamma # T*s
        / voxel_size # T*s/m
        / (TE/2))
    
    time_intervals = numpy.asarray([
        sycomore.bloch.time_interval(
            species, time_step, gradient_amplitude=gradient, position=position)
        for position in positions])
    
    magnetizations = numpy.full((positions_count, steps, 4), m0)
    for step, t in enumerate(times[:-1]):
        if numpy.allclose(t % TR.convert_to(s), 0) and step != len(times)-1:
            pulse = excitation
        elif numpy.allclose(t % TE.convert_to(s), TE.convert_to(s)/2):
            # Time from start of TR
            t_TR = (t%TR.convert_to(s))
            echo = numpy.round((t_TR-TE.convert_to(s)/2)/TE.convert_to(s))
            if echo < train_length:
                pulse = refocalization
            else:
                pulse = numpy.identity(4)
        else:
            pulse = numpy.identity(4)
        magnetizations[:,step+1] = numpy.einsum(
            "ij,oj->oi", pulse, magnetizations[:,step])
        magnetizations[:,step+1] = numpy.einsum(
            "oij,oj->oi", time_intervals, magnetizations[:,step+1])
    
    signals = [m[:,0]+1j*m[:,1] for m in magnetizations]
    phases = numpy.vectorize(numpy.angle)(signals)
    
    magnitude_plot.x = times
    magnitude_plot.y = numpy.abs(numpy.mean(signals, axis=0))
    
    phase_plot.x = times
    phase_plot.y = [numpy.min(phases, axis=0), numpy.max(phases, axis=0)]
    phase_plot.colors = 2*[bqplot.colorschemes.CATEGORY10[0]]
    phase_plot.fill = "between"
    phase_plot.fill_opacities = [0.5]
    phase_plot.stroke_width = 1
    
    stop = time.time()
    widgets["runtime"]["label"].value = f"""Runtime: {utils.to_eng_string(stop-start, "s", 1)}"""

for group in widgets.values():
    for widget in group.values():
        if not isinstance(widget, ipywidgets.widgets.Label):
            widget.observe(update_plot, names="value")

tab = ipywidgets.widgets.HBox([
    ipywidgets.widgets.VBox([
        ipywidgets.widgets.VBox(list(group.values()), layout={"border": "1px solid"}) 
        for group in widgets.values()
    ]),
    ipywidgets.widgets.VBox([magnitude_figure, phase_figure])
])

def init():
    update_plot(None)
