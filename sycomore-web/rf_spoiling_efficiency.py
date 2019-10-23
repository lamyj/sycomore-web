import time

import bqplot.pyplot
import ipywidgets
import numpy
import sycomore
from sycomore.units import *

import utils

name = "RF spoiling (2)"

def rf_spoiling(
        model, flip_angle, TE, TR, slice_thickness, phase_step, repetitions):

    G_readout = 2*numpy.pi*rad / (sycomore.gamma*slice_thickness)
    echoes = numpy.zeros(repetitions, dtype=complex)
    
    for r in range(0, repetitions):
        phase = (phase_step * 1/2*(r+1)*r)

        model.apply_pulse(flip_angle, phase)
        model.apply_time_interval(TE)

        rewind = numpy.exp(-1j*phase.convert_to(rad))
        echoes[r] = model.echo*rewind

        model.apply_time_interval(TR-TE, G_readout/(TR-TE))
    
    return echoes

def compute_ideal_spoiling(species, flip_angle, TR):
    alpha = flip_angle.convert_to(rad)
    E1 = numpy.exp((-TR/species.T1).magnitude)
    signal = numpy.sin(alpha)*(1-E1)/(1-numpy.cos(alpha)*E1)
    return signal

common_attributes = {
    "continuous_update": False, "style": {"description_width": "initial"}}
widgets = {
    "species": {
        "label": ipywidgets.widgets.HTML(value="""<h1 class="group">Species</h1>"""),
        "T1": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=1000, step=1, description="T<sub>1</sub> (ms)",
            **common_attributes),
        "T2": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=1000, step=1, description="T<sub>2</sub> (ms)",
            **common_attributes),
    },
    "sequence": {
        "label": ipywidgets.widgets.HTML(value="""<h1 class="group">Sequence</h1>"""),
        "flip_angle": ipywidgets.widgets.IntSlider(
            min=0, max=90, value=30, step=1, description="Flip angle (°)",
            **common_attributes),
        "TE": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=5, step=1, description="TE (ms)",
            **common_attributes),
        "TR": ipywidgets.widgets.BoundedIntText(
            min=0, max=2000, value=25, step=1, description="TR (ms)",
            **common_attributes),
    },
    "runtime": {"label": ipywidgets.widgets.Label()}
}  

fig_layout = ipywidgets.widgets.Layout(width="750px", height="500px")

figure = bqplot.pyplot.figure(
    legend_location="top-right", 
    fig_margin={"top": 0, "bottom": 30, "left": 60, "right": 20},
    layout=fig_layout)
signal_plot = bqplot.pyplot.plot([], [], labels=["Signal"])
ideal_spoiling_plot = bqplot.pyplot.plot(
    [], [], ":k", labels=["Ideal spoiling"])
bqplot.pyplot.xlabel("Phase increment (°)")
bqplot.pyplot.ylabel("Magnitude")
bqplot.pyplot.ylim(0, 0.6)
bqplot.pyplot.legend()

def update_plot(change):
    start = time.time()
    
    slice_thickness = 1*mm

    species = sycomore.Species(
        widgets["species"]["T1"].value*ms, widgets["species"]["T2"].value*ms)
    
    repetitions = int((4*species.T1/(widgets["sequence"]["TR"].value*ms)).magnitude)
    
    phase_steps = [x*deg for x in range(0, 181)]
    
    steady_states = [
        rf_spoiling(
            sycomore.epg.Regular(species), 
            widgets["sequence"]["flip_angle"].value*deg, 
            widgets["sequence"]["TE"].value*ms, widgets["sequence"]["TR"].value*ms, 
            slice_thickness, phase_step, 
            repetitions)[-1]
        for phase_step in phase_steps]
    
    signal_plot.x = [x.convert_to(deg) for x in phase_steps]
    signal_plot.y = [numpy.abs(x) for x in steady_states]
    
    ideal_spoiling = compute_ideal_spoiling(
        species, widgets["sequence"]["flip_angle"].value*deg, 
        widgets["sequence"]["TR"].value*ms)
    ideal_spoiling_plot.x = [
        phase_steps[0].convert_to(deg), phase_steps[-1].convert_to(deg)]
    ideal_spoiling_plot.y = [ideal_spoiling, ideal_spoiling]
    
    bqplot.pyplot.xlim(
        phase_steps[0].convert_to(deg), phase_steps[-1].convert_to(deg))
    
    stop = time.time()
    widgets["runtime"]["label"].value = f"""Runtime: {utils.to_eng_string(stop-start, "s", 3)}"""

for group in widgets.values():
    for widget in group.values():
        if not isinstance(widget, ipywidgets.widgets.Label):
            widget.observe(update_plot, names="value")

tab = ipywidgets.widgets.HBox([
    ipywidgets.widgets.VBox([
        ipywidgets.widgets.VBox(list(group.values()), layout={"border": "1px solid"}) 
        for group in widgets.values()
    ]),
    figure
])

def init():
    update_plot(None)
