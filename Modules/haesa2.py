def haesa2_required_nc_by_B(lambda_, N, prbSize, limit, reqBw):
    nc = 1
    while nc < limit:
        rho = lambda_ / ( nc * prbSize )
        rn = rho ** N
        B = nc * prbSize * (1 - rn) / (1 - rn * rho)
        if B >= reqBw:
            return nc
        else:
            nc = nc + 1
    return -1


def haesa2_required_nc_by_L(lambda_, N, prbSize, limit, reqLat):
    nc = 1
    while nc < limit:
        rho = lambda_ / ( nc * prbSize )
        rn = rho ** N
        L = (1 + rn * (rho*rho + (N - 2) * rho - N)) * 1000/ (nc * prbSize * (1 - rn * rho) * (1 - rho))
        if L <= reqLat:
            return nc
        else:
            nc = nc + 1
    return -1


def haesa2(slicing):
    N = slicing.N / slicing.numOfSlices

    reqNCs = []
    autoFail = False
    for slice in slicing.slices:
        nc_bw = 0
        nc_lat = 0
        if slice.reqBw:
            nc_bw = haesa2_required_nc_by_B(slice.lambda_, N, slicing.station.PRBbandwidth,
                                            slicing.station.numPRBs, slice.reqBw)
            if nc_bw == -1:
                autoFail = True

        if slice.reqLat:
            nc_lat = haesa2_required_nc_by_L(slice.lambda_, N, slicing.station.PRBbandwidth,
                                             slicing.station.numPRBs, slice.reqLat)
            if nc_lat == -1:
                autoFail = True

        slice.haesa2Result = "HAESA2: Required number of PRB\'s to comply with requirements: " + str(max([nc_bw, nc_lat]))
        reqNCs.append(max([nc_bw, nc_lat]))

    if autoFail or sum(reqNCs) > slicing.station.numPRBs:
        return False
    else:
        return True