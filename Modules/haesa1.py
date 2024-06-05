import numpy as np

def haesa1_L(rho, N, C):
    rn = rho ** N
    return (1 + rn * (rho*rho + (N - 2) * rho - N)) / (C * (1 - rn * rho) * (1 - rho))

def haesa1_B(lambda_, rho, N):
    rn = rho ** N
    return lambda_ * (1 + rn) / (1 + rn * rho)

def haesa1(slicing):
    # HAESA1 represents fully isolated slices with fair distribution of resources
    rho = slicing.station.C / slicing.sumLambda # Common rho for all slices
    calculatedLatency = haesa1_L(rho, slicing.N, slicing.station.C)

    pp = []
    for slice in slicing.slices:
        p = True
        if slice.reqLat:
            if slice.reqLat < calculatedLatency:
                p = False
        if slice.reqBw:
            if slice.reqBw > haesa1_B(slice.lambda_, rho, slicing.N):
                p = False

        if p:
            slice.haesa1Result = "HAESA1: Passed;"
        else:
            slice.haesa1Result = "HAESA1: Failed;"
        pp.append(p)

    return np.prod(pp)