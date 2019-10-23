import time

import bqplot.pyplot
import ipywidgets
import numpy
import sycomore
from sycomore.units import *

import utils

name = "RF spoiling"

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

figure = bqplot.pyplot.figure(
    legend_location="top-right", 
    fig_margin={"top": 0, "bottom": 30, "left": 60, "right": 20})
signal_plot = bqplot.pyplot.plot([], [], labels=["Signal"])
ideal_spoiling_plot = bqplot.pyplot.plot(
    [], [], ":k", labels=["Ideal spoiling"])
bqplot.pyplot.xlabel("Repetition")
bqplot.pyplot.ylabel("Magnitude")
bqplot.pyplot.ylim(0, 0.6)
bqplot.pyplot.legend()

def update_plot(change):
    start = time.time()
    
    slice_thickness = 1*mm

    species = sycomore.Species(T1.value*ms, T2.value*ms)
    model = sycomore.epg.Regular(species)
    
    repetitions = int((4*species.T1/(TR.value*ms)).magnitude)
    
    echoes = rf_spoiling(
        model, flip_angle.value*deg, TE.value*ms, TR.value*ms, slice_thickness, 
        phase_step.value*deg, repetitions)
    
    signal_plot.x = range(repetitions)
    signal_plot.y = numpy.abs(echoes)
    
    ideal_spoiling = compute_ideal_spoiling(
        species, flip_angle.value*deg, TR.value*ms)
    ideal_spoiling_plot.x = [0, repetitions]
    ideal_spoiling_plot.y = [ideal_spoiling, ideal_spoiling]
    
    bqplot.pyplot.xlim(0, repetitions)
    
    stop = time.time()
    runtime.value = f"""Runtime: {utils.to_eng_string(stop-start, "s", 1)}"""

species_label = ipywidgets.widgets.HTML(value="""<div style="text-align:center; font-size: larger">Species</div>""")
T1 = ipywidgets.widgets.BoundedIntText(
    min=0, max=2000, value=1000, step=1, description="T_1 (ms)")
T2 = ipywidgets.widgets.BoundedIntText(
    min=0, max=2000, value=1000, step=1, description="T_2 (ms)")

sequence_label = ipywidgets.widgets.HTML(value="""<div style="text-align:center; font-size: larger">Sequence</div>""")
flip_angle = ipywidgets.widgets.IntSlider(
    min=0, max=90, value=30, step=1, description="Flip angle (°)",
    continuous_update=False, style={"description_width": "initial"})    
TE = ipywidgets.widgets.BoundedIntText(
    min=0, max=2000, value=5, step=1, description="TE (ms)")
TR = ipywidgets.widgets.BoundedIntText(
    min=0, max=2000, value=25, step=1, description="TR (ms)")

phase_step = ipywidgets.widgets.IntSlider(
    min=0, max=180, value=0, step=1, description="Phase step (°)",
    continuous_update=False, style={"description_width": "initial"})

runtime = ipywidgets.widgets.Label()

for widget in [T1, T2, flip_angle, TE, TR, phase_step]:
    widget.observe(update_plot, names="value")

tab = ipywidgets.widgets.HBox([
    ipywidgets.widgets.VBox([
        ipywidgets.widgets.VBox(
            [species_label, T1,T2], 
            layout={"border": "1px solid"}),
        ipywidgets.widgets.VBox(
            [sequence_label, flip_angle, TE, TR, phase_step], 
            layout={"border": "1px solid"}),
        runtime]),
    figure])
