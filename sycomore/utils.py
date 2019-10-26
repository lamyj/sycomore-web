import numpy

def to_eng_string(value, unit, decimals=None):
    """ Format as an engineering string, with SI prefixes
    """
    
    prefixes = {
        24: "Y", 21: "Z", 18: "E", 15: "P", 12: "T", 9: "G", 6: "M", 3: "k",
        0: "",
        -3: "m", -6: "µ", -9: "n", -12: "p", -15: "f", -18: "a", -21: "z", -24: "y",
    }
    
    exponent = numpy.log10(numpy.abs(value))
    eng_exponent = int(exponent - exponent%3)
    prefix = prefixes[eng_exponent]
    mantissa = value/10**eng_exponent
    if decimals is not None:
        mantissa = numpy.round(mantissa)
    return "{} {}{}".format(mantissa, prefix, unit)
