import bqplot.pyplot
import ipywidgets
import numpy
import sycomore
from sycomore.units import *

name = "Slice profile"

figure = bqplot.pyplot.figure(
    legend_location="top-right", 
    fig_margin={"top": 0, "bottom": 30, "left": 60, "right": 20})
transversal_plot = bqplot.pyplot.plot([], [], "-b", labels=["M⟂"])
longitudinal_plot = bqplot.pyplot.plot([], [], "-g", labels=["M∥"])
bqplot.pyplot.xlabel("Position (mm)")
bqplot.pyplot.ylabel("Magnitude")
bqplot.pyplot.legend()

def update_plot(change):
    slice_thickness = 1*mm
    pulse_support_size = 101

    t0 = pulse_duration.value*ms/(2*zero_crossings.value)

    support = sycomore.linspace(pulse_duration.value*ms, pulse_support_size)
    envelope = sycomore.sinc_envelope(t0)
    bandwidth = 1/t0

    sinc_pulse = sycomore.HardPulseApproximation(
        sycomore.Pulse(flip_angle.value*deg, 0*deg), support, envelope, 
        bandwidth, slice_thickness/2, "")
    gradient_duration = sinc_pulse.get_time_interval().duration
    gradient_amplitude = (
        sinc_pulse.get_time_interval().gradient_moment[2]
        /(2*numpy.pi*sycomore.gamma)
        /sinc_pulse.get_time_interval().duration)
    
    species = sycomore.Species(T1.value*ms, T2.value*ms)
    
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
    
    x_axis = numpy.asarray([
        (2*numpy.pi*x/sinc_pulse.get_gradient_moment()[2]).convert_to(mm) 
        for x in range(len(M_transversal))])
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

species_label = ipywidgets.widgets.HTML(value="""<div style="text-align:center; font-size: larger">Species</div>""")
T1 = ipywidgets.widgets.BoundedIntText(
    min=0, max=2000, value=1000, step=1, description="T_1 (ms)")
T2 = ipywidgets.widgets.BoundedIntText(
    min=0, max=2000, value=100, step=1, description="T_2 (ms)")

pulse_label = ipywidgets.widgets.HTML(value="""<div style="text-align:center; font-size: larger">Pulse</div>""")
flip_angle = ipywidgets.widgets.IntSlider(
    min=0, max=90, value=90, step=1, description="Flip angle (°)",
    continuous_update=False, style={"description_width": "initial"})
pulse_duration = ipywidgets.widgets.BoundedIntText(
    min=1, max=20, value=10, step=1, description="Duration (ms)",
    continuous_update=False, style={"description_width": "initial"})
zero_crossings = ipywidgets.widgets.BoundedIntText(
    min=1, max=20, value=10, step=1, description="Zero-crossings",
    continuous_update=False, style={"description_width": "initial"})

for widget in [T1, T2, flip_angle, pulse_duration, zero_crossings]:
    widget.observe(update_plot, names="value")

tab = ipywidgets.widgets.HBox([
    ipywidgets.widgets.VBox([
        ipywidgets.widgets.VBox(
            [species_label, T1,T2], 
            layout={"border": "1px solid"}),
        ipywidgets.widgets.VBox(
            [pulse_label, flip_angle, pulse_duration, zero_crossings], 
            layout={"border": "1px solid"})]),
    figure])

update_plot(None)
