import bqplot.pyplot
import ipywidgets
import numpy
import sycomore
from sycomore.units import *

name = "Slice profile"

figure = bqplot.pyplot.figure(
    legend_location="top-right", 
    fig_margin={"top": 0, "bottom": 30, "left": 60, "right": 20})
transversal_plot = bqplot.pyplot.plot([], [], "-b", labels=["M∥"])
longitudinal_plot = bqplot.pyplot.plot([], [], "-g", labels=["M⟂"])
bqplot.pyplot.xlabel("Position (mm)")
bqplot.pyplot.ylabel("Magnitude")
bqplot.pyplot.legend()

def update_plot(change):
    slice_thickness = 1*mm
    pulse_support_size = 101
    sampling_support_size = 501

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
    model = sycomore.epg.Regular(species)
    for hard_pulse in sinc_pulse.get_pulses():
        model.apply_pulse(hard_pulse.angle, hard_pulse.phase)
        model.apply_time_interval(gradient_duration, gradient_amplitude)

    # Unfold the F and the Z states
    F = numpy.hstack((model.states[:,0], numpy.conj(model.states[1:,1][::-1])))
    Z = numpy.hstack((model.states[:,2], model.states[1:,2][::-1]))

    # Perform iFFT, and shift it since the spatial axis must be centered on zero.
    M_transversal = numpy.fft.fftshift(numpy.fft.ifft(F))
    M_longitudinal = numpy.fft.fftshift(numpy.fft.ifft(Z))
    
    # NOTE: with 1-D EPG, the slice-selection gradient is played on the first/only 
    # axis, which is also the readout axis. The roles of transversal and 
    # longitudinal are thus flipped.
    x_axis = numpy.asarray([
        (2*numpy.pi*x/sinc_pulse.get_gradient_moment()[2]).convert_to(mm) 
        for x in range(len(M_transversal))])
    x_axis -= 0.5*(x_axis[0]+x_axis[-1])
    
    transversal_plot.x = x_axis
    transversal_plot.y = numpy.abs(M_transversal)
    
    longitudinal_plot.x = x_axis
    longitudinal_plot.y = numpy.abs(M_longitudinal)
    
    bqplot.pyplot.xlim(-slice_thickness.convert_to(mm), slice_thickness.convert_to(mm))

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
