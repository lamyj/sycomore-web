import time

import bokeh.layouts
import bokeh.models
import bokeh.palettes
import bokeh.plotting
import numpy
import sycomore
from sycomore.units import *

import utils

title = "Slice profile"

def create_contents():
    # Species controls
    T1 = bokeh.models.Slider(
        id="T1", title="T1 (ms)", value=600, start=0, end=2000, step=1)
    T2 = bokeh.models.Slider(
        id="T2", title="T2 (ms)", value=400, start=0, end=2000, step=1)
    
    # Pulse controls
    flip_angle = bokeh.models.Slider(
        id="flip_angle", title="Flip angle (°)",
        value=90, start=0, end=90, step=1)
    duration = bokeh.models.Slider(
        id="duration", title="Duration (ms)", value=10, start=1, end=20, step=1)
    zero_crossings = bokeh.models.Slider(
        id="zero_crossings", title="Zero crossings",
        value=10, start=0, end=20, step=1)

    # Data sources
    longitudinal_data = bokeh.models.ColumnDataSource(
        id="longitudinal_data", data={"x": [], "y": []})
    transversal_data = bokeh.models.ColumnDataSource(
        id="transversal_data", data={"x": [], "y": []})
    
    # Magnitude plot
    magnitude_plot = bokeh.plotting.figure(
        id="magnitude_plot",
        aspect_ratio=1.5,
        title="", sizing_mode="scale_both", toolbar_location=None,
        margin=[0,50,0,0])
    magnitude_plot.xaxis.axis_label = "Position (mm)"
    magnitude_plot.yaxis.axis_label = "Magnitude"
    magnitude_plot.x_range.range_padding = 0
    magnitude_plot.y_range.start=0
    magnitude_plot.line(
        # Category 10
        x="x", y="y", source=longitudinal_data, legend="M∥", 
        color=bokeh.palettes.Category10_3[0])
    magnitude_plot.line(
        x="x", y="y", source=transversal_data, legend="M⟂", 
        color=bokeh.palettes.Category10_3[1])
    
    # Interactions
    for control in [T1, T2, flip_angle, duration, zero_crossings]:
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
            bokeh.models.Div(text="Pulse", css_classes=["group-title"]),
            flip_angle, duration, zero_crossings,
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
    
    pulse_support_size = 101
    
    T1 = document.get_model_by_id("T1").value*ms
    T2 = document.get_model_by_id("T2").value*ms
    
    flip_angle = document.get_model_by_id("flip_angle").value*deg
    duration = document.get_model_by_id("duration").value*ms
    zero_crossings = document.get_model_by_id("zero_crossings").value

    t0 = duration/(2*zero_crossings)

    support = sycomore.linspace(duration, pulse_support_size)
    envelope = sycomore.sinc_envelope(t0)
    bandwidth = 1/t0

    sinc_pulse = sycomore.HardPulseApproximation(
        sycomore.Pulse(flip_angle, 0*deg), 
        support, envelope, bandwidth, slice_thickness, "")
    gradient_duration = sinc_pulse.get_time_interval().duration
    gradient_amplitude = (
        sinc_pulse.get_time_interval().gradient_moment[2]
        /(2*numpy.pi*sycomore.gamma)
        /sinc_pulse.get_time_interval().duration)
    
    species = sycomore.Species(T1, T2)
    pulse_step = sycomore.TimeInterval(
        gradient_duration, [0*T/m, 0*T/m, gradient_amplitude])
    
    model = sycomore.epg.Discrete3D(species)
    for index, hard_pulse in enumerate(sinc_pulse.get_pulses()):
        model.apply_pulse(hard_pulse.angle, hard_pulse.phase)
        model.apply_time_interval(pulse_step)
    
    # Unfold the F and the Z states: create an array for all orders, including
    # empty ones.
    max_order = numpy.max(model.orders, axis=0)[2]
    max_bin = int(max_order/model.bin_width)
    F = numpy.zeros(2*max_bin+1, model.states.dtype)
    Z = numpy.zeros(2*max_bin+1, model.states.dtype)
    for order, state in zip(model.orders, model.states):
        bin = int(order[2]/model.bin_width)
        # WARNING: since we de-bin the orders, we need to scale the population
        F[bin] = F.shape[0]*state[0]
        Z[bin] = F.shape[0]*state[2]
        
        if order != 0:
            F[-bin] = F.shape[0]*state[1].conj()
            Z[-bin] = F.shape[0]*state[2]
    
    # Perform iFFT, and shift it since the spatial axis must be centered on zero.
    M_transversal = numpy.fft.fftshift(numpy.fft.ifft(F))
    M_longitudinal = numpy.fft.fftshift(numpy.fft.ifft(Z))
    
    # Frequency ranges from -max_order to +max_order: the spatial step size
    # is then given by the following expression.
    step = (1/(2*max_order)).convert_to(mm)
    
    x_axis = step*numpy.arange(len(M_transversal))
    x_axis -= 0.5*(x_axis[0]+x_axis[-1])
    
    # Crop between [-slice_thickness, +slice_thickness]
    slice_ = (
        numpy.searchsorted(x_axis, -slice_thickness.convert_to(mm), "left"),
        numpy.searchsorted(x_axis, +slice_thickness.convert_to(mm), "right"),
    )
    x_axis = x_axis[slice_[0]:slice_[1]]
    M_transversal = M_transversal[slice_[0]:slice_[1]]
    M_longitudinal = M_longitudinal[slice_[0]:slice_[1]]
    
    transversal_data = document.get_model_by_id("transversal_data")
    transversal_data.data = { "x": x_axis, "y": numpy.abs(M_transversal) }
    
    longitudinal_data = document.get_model_by_id("longitudinal_data")
    longitudinal_data.data = { "x": x_axis, "y": numpy.abs(M_longitudinal) }
    
    stop = time.time()
    document.get_model_by_id("runtime").text = "Runtime: {}".format(
        utils.to_eng_string(stop-start, "s", 3))

def init():
    update()
