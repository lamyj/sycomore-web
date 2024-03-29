import time

import bokeh.layouts
import bokeh.models
import bokeh.plotting
import numpy
import sycomore
from sycomore.units import *

import utils

title = "RARE"

time_step = 5*ms

def create_contents():
    # Species controls
    T1 = bokeh.models.Slider(
        id="T1", title="T1 (ms)", value=600, start=0, end=2000, step=1)
    T2 = bokeh.models.Slider(
        id="T2", title="T2 (ms)", value=400, start=0, end=2000, step=1)
    
    # Sequence controls
    excitation = bokeh.models.Slider(
        id="excitation", title="Excitation pulse (°)", 
        value=90, start=0, end=180, step=1)
    TE = bokeh.models.Slider(
        id="TE", title="TE (ms)", 
        value=200, start=0, end=2000, step=2*time_step.convert_to(ms))
    refocalization = bokeh.models.Slider(
        id="refocalization", title="Refocalization pulse (°)", 
        value=180, start=0, end=180, step=1)
    train_length = bokeh.models.Slider(
        id="train_length", title="Train length", 
        value=3, start=1, end=10, step=1)
    TR = bokeh.models.Slider(
        id="TR", title="TR (ms)", 
        value=1000, start=0, end=2000, step=2*time_step.convert_to(ms))
    repetitions = bokeh.models.Slider(
        id="repetitions", title="Repetitions", value=4, start=1, end=10, step=1)
    
    # Data sources
    magnitude_data = bokeh.models.ColumnDataSource(
        id="magnitude_data", data={"x": [], "y": []})
    phase_data = bokeh.models.ColumnDataSource(
        id="phase_data", data={"x": [], "y_min": [], "y_max": []})
    
    # Magnitude plot
    magnitude_plot = bokeh.plotting.figure(
        id="magnitude_plot",
        aspect_ratio=3,
        title="", sizing_mode="scale_both", toolbar_location=None,
        margin=[0,50,0,0])
    magnitude_plot.yaxis.axis_label = "Magnitude"
    magnitude_plot.x_range.range_padding = 0
    magnitude_plot.y_range.start=0
    magnitude_plot.y_range.end=1
    magnitude_plot.line(x="x", y="y", source=magnitude_data)
    
    # Phase plot
    phase_plot = bokeh.plotting.figure(
        id="phase_plot",
        aspect_ratio=3,
        title="", sizing_mode="scale_both", toolbar_location=None, 
        margin=[0,50,0,0])
    phase_plot.xaxis.axis_label = "Time (ms)"
    phase_plot.yaxis.axis_label = "Phase (rad)"
    phase_plot.x_range.range_padding = 0
    phase_plot.varea(x="x", y1="y_min", y2="y_max", source=phase_data)
    
    # Interactions
    for control in [T1, T2, excitation, TE, refocalization, train_length, TR, repetitions]:
        control.on_change("value_throttled", lambda attr, old, new: update())
    T1.js_link("value_throttled", T2, "end")
    T1.on_change(
        "value_throttled", 
        lambda attr, old, new: T2.update(
            end=min(new, T2.end), value=min(new, T2.value)))
    
    # Layout
    inputs = bokeh.layouts.column(
        bokeh.layouts.column(
            bokeh.models.Div(text="Species", css_classes=["group-title"]), T1, T2, 
            css_classes=["box"]), 
        bokeh.layouts.column(
            bokeh.models.Div(text="Sequence", css_classes=["group-title"]),
            excitation, TE, refocalization, train_length, TR, repetitions,
            css_classes=["box"]),
        bokeh.models.Div(id="runtime", text="Runtime: ", align="start"),
        width=320, height=250,
        sizing_mode="fixed")
    return bokeh.layouts.layout(
        [
            [inputs, [magnitude_plot, phase_plot]]
        ], 
        sizing_mode="scale_both")

def update():
    start = time.time()
    
    document = bokeh.plotting.curdoc()
    
    T1 = document.get_model_by_id("T1").value*ms
    T2 = document.get_model_by_id("T2").value*ms
    
    excitation = document.get_model_by_id("excitation").value*deg
    TE = document.get_model_by_id("TE").value*ms
    refocalization = document.get_model_by_id("refocalization").value*deg
    train_length = document.get_model_by_id("train_length").value
    TR = document.get_model_by_id("TR").value*ms
    repetitions = document.get_model_by_id("repetitions").value
    
    species = sycomore.Species(T1, T2)
    
    m0 = [0., 0., 1., 1.]
    
    voxel_size = 1*mm
    positions_count = 192
    
    steps = 1+int(repetitions*TR/time_step)
    times_ms = numpy.linspace(0, (repetitions*TR).convert_to(ms), steps)

    excitation = sycomore.bloch.pulse(excitation, 90*deg)
    refocalization = sycomore.bloch.pulse(refocalization, 0*rad)
        
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
    # WARNING: floating-point modulo arithmetic is not reliable (pulses are
    # missed). Switch to integer arithmetic in ms; this assumes that 
    # time_step >= 2*ms.
    TE_ms = int(numpy.round(TE.convert_to(ms)))
    TR_ms = int(numpy.round(TR.convert_to(ms)))
    for step, t in enumerate(times_ms[:-1]):
        
        t_in_TR = int(numpy.round(t)) % TR_ms
        t_in_TE = t_in_TR % TE_ms
        
        if t_in_TR == 0 and step != len(times_ms)-1:
            pulse = excitation
        elif t_in_TE == TE_ms//2:
            echo = (t_in_TR-TE_ms//2)//TE_ms
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
    phases = numpy.angle(signals)
    
    magnitude_data = document.get_model_by_id("magnitude_data")
    magnitude_data.data = {
        "x": times_ms, 
        "y": numpy.abs(numpy.mean(signals, axis=0)) }
    
    phase_data = document.get_model_by_id("phase_data")
    phase_data.data = {
        "x": times_ms, 
        "y_min": numpy.min(phases, axis=0), "y_max": numpy.max(phases, axis=0) }
    
    stop = time.time()
    document.get_model_by_id("runtime").text = "Runtime: {}".format(
        utils.to_eng_string(stop-start, "s", 1))
    
def init():
    update()
