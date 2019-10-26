import time

import bokeh.layouts
import bokeh.models
import bokeh.plotting
import numpy
import sycomore
from sycomore.units import *

from rf_spoiling import *
import utils

title = "RF-Spoiling (efficiency)"

def create_contents():
    # Species controls
    T1 = bokeh.models.Slider(
        id="T1", title="T1 (ms)", 
        value=1000, start=0, end=2000, step=1, callback_policy="mouseup")
    T2 = bokeh.models.Slider(
        id="T2", title="T2 (ms)", 
        value=1000, start=0, end=2000, step=1, callback_policy="mouseup")
    
    # Sequence controls
    flip_angle = bokeh.models.Slider(
        id="flip_angle", title="Flip angle (°)",
        value=30, start=0, end=90, step=1, callback_policy="mouseup")
    TE = bokeh.models.Slider(
        id="TE", title="TE (ms)",
        value=5, start=0, end=2000, step=1, callback_policy="mouseup")
    TR = bokeh.models.Slider(
        id="TR", title="TR (ms)",
        value=25, start=0, end=2000, step=1, callback_policy="mouseup")

    # Data sources
    magnitude_data = bokeh.models.ColumnDataSource(
        id="magnitude_data", data={"x": [], "y": []})
    ideal_spoiling_data = bokeh.models.ColumnDataSource(
        id="ideal_spoiling_data", data={"x": [], "y": []})

    # Magnitude plot
    magnitude_plot = bokeh.plotting.figure(
        id="magnitude_plot",
        aspect_ratio=1.5,
        title="", sizing_mode="scale_both", toolbar_location=None)
    magnitude_plot.xaxis.axis_label = "Repetition"
    magnitude_plot.yaxis.axis_label = "Magnitude"
    magnitude_plot.x_range.range_padding = 0
    magnitude_plot.y_range.start=0
    # magnitude_plot.y_range.end=1
    magnitude_plot.line(x="x", y="y", source=magnitude_data, legend="Signal")
    magnitude_plot.line(
        x="x", y="y", source=ideal_spoiling_data, 
        legend="Ideal spoiling", color="black", line_dash="dashed")

    # Interactions
    for control in [T1, T2, flip_angle, TE, TR]:
        control.on_change("value_throttled", lambda attr, old, new: update())

    # Layout
    inputs = bokeh.layouts.column(
        bokeh.layouts.column(
            bokeh.models.Div(text="Species", css_classes=["group-title"]), T1, T2, 
            css_classes=["box"]), 
        bokeh.layouts.column(
            bokeh.models.Div(text="Sequence", css_classes=["group-title"]),
            flip_angle, TE, TR,
            css_classes=["box"]),
        bokeh.models.Div(id="runtime", text="Runtime: ", align="start"),
        width=320, height=250,
        sizing_mode="fixed")
    return bokeh.layouts.layout(
        [
            [inputs, magnitude_plot]
        ], 
        sizing_mode="scale_both")

def update():
    start = time.time()
    
    slice_thickness = 1*mm
    
    document = bokeh.plotting.curdoc()
    
    T1 = document.get_model_by_id("T1").value*ms
    T2 = document.get_model_by_id("T2").value*ms
    
    flip_angle = document.get_model_by_id("flip_angle").value*deg
    TE = document.get_model_by_id("TE").value*ms
    TR = document.get_model_by_id("TR").value*ms
    
    species = sycomore.Species(T1, T2)
    repetitions = int((4*species.T1/TR).magnitude)
    
    phase_steps = [x*deg for x in numpy.arange(0, 181, 1.5)]
    
    steady_states = [
        rf_spoiling(
            sycomore.epg.Regular(species), 
            flip_angle, TE, TR, slice_thickness, phase_step, repetitions
        )[-1]
        for phase_step in phase_steps]
    
    magnitude_data = document.get_model_by_id("magnitude_data")
    magnitude_data.data = {
        "x": [x.convert_to(deg) for x in phase_steps], 
        "y": [numpy.abs(x) for x in steady_states] }
    
    ideal_spoiling = compute_ideal_spoiling(species, flip_angle, TR)
    ideal_spoiling_data = document.get_model_by_id("ideal_spoiling_data")
    ideal_spoiling_data.data = {
        "x": (phase_steps[0].convert_to(deg), phase_steps[-1].convert_to(deg)), 
        "y": (ideal_spoiling, ideal_spoiling) }
    
    stop = time.time()
    document.get_model_by_id("runtime").text = "Runtime: {}".format(
        utils.to_eng_string(stop-start, "s", 3))

def init():
    update()
