import numpy as np

def haesa1_L(rho, N, C):
    rn = rho ** N
    return (1 + rn * (rho*rho + (N - 2) * rho - N)) * 1000/ (C * (1 - rn * rho) * (1 - rho))

def haesa1_B(rho, N, C, k):
    rn = rho ** (N/k)
    return C * (1 + rn) / ((1 + rn * rho) * k)

def haesa1(slicing):
    # HAESA1 represents fully isolated slices with fair distribution of resources
    rho = slicing.sumLambda / slicing.station.C # Common rho for all slices
    calculatedLatency = haesa1_L(rho, slicing.N, slicing.station.C)
    calculatedBandwidth = haesa1_B(rho, slicing.N, slicing.station.C, slicing.numOfSlices)

    pp = []
    for slice in slicing.slices:
        p = True
        if slice.reqBw:
            if slice.reqBw > calculatedBandwidth:
                p = False
        if slice.reqLat:
            if slice.reqLat < calculatedLatency:
                p = False

        if p:
            slice.haesa1Result = 'HAESA1: Passed; ' + 'B = ' + str(round(calculatedBandwidth, 2)) + \
                                        ' mbps and L = ' + str(round(calculatedLatency, 2)) + ' ms.'
        else:
            slice.haesa1Result = 'HAESA1: Failed; ' + 'B = ' + str(round(calculatedBandwidth, 2)) + \
                                        ' mbps and L = ' + str(round(calculatedLatency, 2)) + ' ms.'
        pp.append(p)

    return np.prod(pp)