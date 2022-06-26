import time

import bokeh.layouts
import bokeh.models
import bokeh.palettes
import bokeh.plotting
import numpy
import sycomore
from sycomore.units import *

import utils

title = "Spin echo contrasts"

fixed_T1 = 1000*ms
fixed_T2 = 100*ms

presets = {
    "T1-weighted": (10*ms, 600*ms),
    "T2-weighted": (100*ms, 3000*ms),
    "PD-weighted": (10*ms, 3000*ms),
}

def create_contents():
    default_contrast = "T1-weighted"
    default_TE, default_TR = [
        x.convert_to(ms) for x in presets[default_contrast]]
    
    # Sequence controls
    excitation = bokeh.models.Slider(
        id="excitation", title="Excitation pulse (°)", 
        value=90, start=0, end=180, step=1)
    TE = bokeh.models.Slider(
        id="TE", title="TE (ms)", value=default_TE, start=0, end=200, step=10)
    refocalization = bokeh.models.Slider(
        id="refocalization", title="Refocalization pulse (°)", 
        value=180, start=0, end=180, step=1)
    TR = bokeh.models.Slider(
        id="TR", title="TR (ms)", value=default_TR, start=0, end=3000, step=10)
    preset = bokeh.models.Select(
        id="preset", title="Contrast", options=list(presets.keys()),
        value=default_contrast)
    
    # Data sources
    T1_data = bokeh.models.ColumnDataSource(
        id="T1_data", data={"x": [], "y": []})
    T2_data = bokeh.models.ColumnDataSource(
        id="T2_data", data={"x": [], "y": []})
    
    # T1 plot
    T1_plot = bokeh.plotting.figure(
        id="T1_plot",
        aspect_ratio=3,
        title="", sizing_mode="scale_both", toolbar_location=None,
        margin=[0,50,0,0])
    T1_plot.yaxis.axis_label = "Magnitude"
    T1_plot.xaxis.axis_label = "T1 (ms), T2={} ms".format(
        int(fixed_T2.convert_to(ms)))
    T1_plot.x_range.range_padding = 0
    T1_plot.y_range.start=0
    # T1_plot.y_range.end=1
    T1_plot.line(x="x", y="y", source=T1_data)
    
    # T2 plot
    T2_plot = bokeh.plotting.figure(
        id="T2_plot",
        aspect_ratio=3,
        title="", sizing_mode="scale_both", toolbar_location=None,
        margin=[0,50,0,0])
    T2_plot.yaxis.axis_label = "Magnitude"
    T2_plot.xaxis.axis_label = "T2 (ms), T1={} ms".format(
        int(fixed_T1.convert_to(ms)))
    T2_plot.x_range.range_padding = 0
    T2_plot.y_range.start=0
    # T2_plot.y_range.end=1
    T2_plot.line(x="x", y="y", source=T2_data)
    
    # Interactions
    for control in [excitation, TE, refocalization, TR]:
        control.on_change("value_throttled", lambda attr, old, new: update())
    preset.on_change("value", lambda attr, old, new: set_preset())
    
    # Layout
    inputs = bokeh.layouts.column(
        bokeh.layouts.column(
            bokeh.models.Div(text="Sequence", css_classes=["group-title"]),
            excitation, TE, refocalization, TR, preset,
            css_classes=["box"]),
        bokeh.models.Div(id="runtime", text="Runtime: ", align="start"),
        width=320, height=250,
        sizing_mode="fixed")
    return bokeh.layouts.layout(
        [
            [inputs, [T1_plot, T2_plot]]
        ], 
        sizing_mode="scale_both")

def update():
    start = time.time()
    
    document = bokeh.plotting.curdoc()
    
    excitation = document.get_model_by_id("excitation").value*deg
    TE = document.get_model_by_id("TE").value*ms
    refocalization = document.get_model_by_id("refocalization").value*deg
    TR = document.get_model_by_id("TR").value*ms
    
    T1_array = sycomore.linspace(0*s, 1*s, 20)
    T2_array = sycomore.linspace(0*s, 1*s, 20)
    
    T1_signal = [
        simulate_spin_echo(
            sycomore.Species(T1, fixed_T2),
            excitation, TE, refocalization, TR)
        for T1 in T1_array]
    T2_signal = [
        simulate_spin_echo(
            sycomore.Species(fixed_T1, T2),
            excitation, TE, refocalization, TR)
        for T2 in T2_array]
    
    T1_data = document.get_model_by_id("T1_data")
    T1_data.data = {
        "x": [x.convert_to(ms) for x in T1_array], "y": numpy.abs(T1_signal) }
    
    T2_data = document.get_model_by_id("T2_data")
    T2_data.data = {
        "x": [x.convert_to(ms) for x in T2_array], "y": numpy.abs(T2_signal) }
    
    stop = time.time()
    document.get_model_by_id("runtime").text = "Runtime: {}".format(
        utils.to_eng_string(stop-start, "s", 1))

def set_preset():
    document = bokeh.plotting.curdoc()
    TE, TR = presets[document.get_model_by_id("preset").value]
    document.get_model_by_id("TE").value = TE.convert_to(ms)
    document.get_model_by_id("TR").value = TR.convert_to(ms)
    update()

def simulate_spin_echo(species, excitation, TE, refocalization, TR):
    model = sycomore.epg.Discrete(species)
    model.threshold = 1e-3
    signal = 0
    gradient = sycomore.TimeInterval(TE/2, 1*mT/m)
    for i in range(150):
        model.apply_pulse(excitation)
        model.apply_time_interval(gradient)
        model.apply_pulse(refocalization)
        model.apply_time_interval(gradient)
        signal = model.echo
        model.apply_time_interval(gradient)
        model.apply_time_interval(TR-TE/2)
    return signal

def init():
    update()
