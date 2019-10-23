import time

import bqplot.pyplot
import ipywidgets
import numpy
import sycomore
from sycomore.units import *

import utils

name = "Slice profile"

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
    "pulse": {
        "label": ipywidgets.widgets.HTML(value="""<h1 class="group">Pulse</h1>"""),
        "flip_angle": ipywidgets.widgets.IntSlider(
            min=0, max=90, value=90, step=1, description="Flip angle (°)",
            continuous_update=False, style={"description_width": "initial"}),
        "duration": ipywidgets.widgets.BoundedIntText(
            min=1, max=20, value=10, step=1, description="Duration (ms)",
            continuous_update=False, style={"description_width": "initial"}),
        "zero_crossings": ipywidgets.widgets.BoundedIntText(
            min=1, max=20, value=10, step=1, description="Zero-crossings",
            continuous_update=False, style={"description_width": "initial"}),
    },
    "runtime": {"label": ipywidgets.widgets.Label()}
}


fig_layout = ipywidgets.widgets.Layout(width="750px", height="500px")

figure = bqplot.pyplot.figure(
    legend_location="top-right", 
    fig_margin={"top": 0, "bottom": 30, "left": 60, "right": 20},
    layout=fig_layout)
transversal_plot = bqplot.pyplot.plot([], [], "-b", labels=["M⟂"])
longitudinal_plot = bqplot.pyplot.plot([], [], "-g", labels=["M∥"])
bqplot.pyplot.xlabel("Position (mm)")
bqplot.pyplot.ylabel("Magnitude")
bqplot.pyplot.legend()

def update_plot(change):
    start = time.time()
    
    slice_thickness = 1*mm
    pulse_support_size = 101

    t0 = widgets["pulse"]["duration"].value*ms/(2*widgets["pulse"]["zero_crossings"].value)

    support = sycomore.linspace(widgets["pulse"]["duration"].value*ms, pulse_support_size)
    envelope = sycomore.sinc_envelope(t0)
    bandwidth = 1/t0

    sinc_pulse = sycomore.HardPulseApproximation(
        sycomore.Pulse(widgets["pulse"]["flip_angle"].value*deg, 0*deg), 
        support, envelope, bandwidth, slice_thickness/2, "")
    gradient_duration = sinc_pulse.get_time_interval().duration
    gradient_amplitude = (
        sinc_pulse.get_time_interval().gradient_moment[2]
        /(2*numpy.pi*sycomore.gamma)
        /sinc_pulse.get_time_interval().duration)
    
    species = sycomore.Species(
        widgets["species"]["T1"].value*ms, widgets["species"]["T2"].value*ms)
    
    model = sycomore.epg.Discrete3D(species)
    for index, hard_pulse in enumerate(sinc_pulse.get_pulses()):
        model.apply_pulse(hard_pulse.angle, hard_pulse.phase)
        model.apply_time_interval(
            gradient_duration, [0*T/m, 0*T/m, gradient_amplitude])

    # Unfold the F and the Z states: create an array for all orders, including
    # empty ones
    orders = numpy.reshape(model.orders, (-1,3))[:,2]
    orders = [int(x.magnitude) for x in orders / model.bin_width]
    F = numpy.zeros(2*max(orders)+1, model.states.dtype)
    Z = numpy.zeros(2*max(orders)+1, model.states.dtype)
    for order, state in zip(orders, model.states):
        F[order] = state[0]
        Z[order] = state[2]
        
        if order != 0:
            F[-order] = state[1].conj()
            Z[-order] = state[2]
    
    # Perform iFFT, and shift it since the spatial axis must be centered on zero.
    M_transversal = numpy.fft.fftshift(numpy.fft.ifft(F, norm="ortho"))
    M_longitudinal = numpy.fft.fftshift(numpy.fft.ifft(Z, norm="ortho"))
    
    step = (2*numpy.pi/sinc_pulse.get_gradient_moment()[2]).convert_to(mm)
    # The following line is almost 400 ms
    x_axis = numpy.asarray([step*x for x in range(len(M_transversal))])
    x_axis -= 0.5*(x_axis[0]+x_axis[-1])
    
    # Crop between [-slice_thickness, +slice_thickness]
    slice_ = (
        numpy.searchsorted(x_axis, -slice_thickness.convert_to(mm), "left"),
        numpy.searchsorted(x_axis, +slice_thickness.convert_to(mm), "right"),
    )
    x_axis = x_axis[slice_[0]:slice_[1]]
    M_transversal = M_transversal[slice_[0]:slice_[1]]
    M_longitudinal = M_longitudinal[slice_[0]:slice_[1]]
    
    transversal_plot.x = x_axis
    transversal_plot.y = numpy.abs(M_transversal)
    
    longitudinal_plot.x = x_axis
    longitudinal_plot.y = numpy.abs(M_longitudinal)
    
    bqplot.pyplot.xlim(x_axis[0], x_axis[-1])
    
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
    figure
])

def init():
    update_plot(None)
