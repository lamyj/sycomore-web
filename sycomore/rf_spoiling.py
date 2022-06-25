import numpy
import sycomore
from sycomore.units import *

def rf_spoiling(
        model, flip_angle, TE, TR, slice_thickness, phase_step, repetitions):

    t_readout = TR-TE
    G_readout = (2*numpy.pi*rad / (sycomore.gamma*slice_thickness))/(TR-TE)
    readout = sycomore.TimeInterval(t_readout, G_readout)
    
    echoes = numpy.zeros(repetitions, dtype=complex)
    
    for r in range(0, repetitions):
        phase = (phase_step * 1/2*(r+1)*r)

        model.apply_pulse(flip_angle, phase)
        model.apply_time_interval(TE)

        echoes[r] = model.echo*numpy.exp(-1j*phase.convert_to(rad))

        model.apply_time_interval(readout)
    
    return echoes

def compute_ideal_spoiling(species, flip_angle, TR):
    alpha = flip_angle.convert_to(rad)
    E1 = numpy.exp((-TR/species.T1))
    signal = numpy.sin(alpha)*(1-E1)/(1-numpy.cos(alpha)*E1)
    return float(signal)
