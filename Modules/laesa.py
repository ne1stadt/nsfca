import threading
import numpy as np
import itertools

NUM_OF_THREADS = 8
STEP = 10

def get_possible_N(slicing):
    iterables = [range(1, slicing.N)] * (slicing.numOfSlices + 1)
    fullCombinations = list(itertools.product(*iterables))
    l = len(fullCombinations)
    for i in range(l-1, -1, -1):
        if sum(fullCombinations[i]) != slicing.N:
            fullCombinations.pop(i)
    return list(map(lambda x: {'N': x[:-1], 'N0': x[-1]}, fullCombinations))
    # eg. return [{'N': [5, 5, 5], 'N0': 6}]


def condition(slicing, combination):
    nominator = 0
    denominator = 0
    for i in range(slicing.numOfSlices):
        c = combination['cn'][i] * slicing.station.PRBbandwidth
        r = slicing.slices[i].lambda_ / c
        rn = r ** combination['N'][i]
        ploss = rn * (1 - r) / (1 - rn*r)
        nominator = nominator + slicing.slices[i].lambda_ * ploss
        denominator = denominator + slicing.slices[i].lambda_ * ploss / c

    if sum(combination['cn']) * slicing.station.PRBbandwidth + (nominator / denominator) > slicing.station.C:
        return False, denominator
    else:
        return True, denominator


def get_possible_CN(slicing, possibleN):
    iterables = [range(1, slicing.station.numPRBs, STEP)] * (slicing.numOfSlices)
    cCombinations = list(itertools.product(*iterables))
    fullCombinations = list(map(lambda x, y: {'cn': x, 'N': y['N'], 'N0': y['N0']}, cCombinations, possibleN))

    l = len(fullCombinations)
    for i in range(l - 1, -1, -1):
        if sum(fullCombinations[i]['cn']) > slicing.station.numPRBs:
            fullCombinations.pop(i)

    l = len(fullCombinations)

    for i in range(l-1, -1, -1):
        result, rho0 = condition(slicing, fullCombinations[i])
        if result:
            fullCombinations[i]['rho0'] = rho0
        else:
            fullCombinations.pop(i)
    return fullCombinations
    # eg. return [{'cn': [45, 45, 45], 'N': [5, 5, 5], 'rho0': 1, 'N0': 6}]


def B(slicing, combination, i):
    r = slicing.slices[i].lambda_ / (combination['cn'][i] * slicing.station.PRBbandwidth)
    rn = r ** combination['N'][i]
    r0n0 = combination['rho0'] ** combination['N0']
    return (slicing.slices[i].lambda_ / (1 - rn * r)) * \
           (1 - rn * (1 - ((1 - r) * (1 - r0n0) / (1 - r0n0 * combination['rho0']))))


def L_helper(r, N, rn):
    return (1 + rn * (r*r + (N - 2)*r - N)) / ((1 - rn*r) * (1 - r))


def L(slicing, combination, i):
    c0 = slicing.station.numPRBs - sum(combination['cn'])
    r0n0 = combination['rho0'] ** combination['N0']
    ci = combination['cn'][i] * slicing.station.PRBbandwidth
    r = slicing.slices[i].lambda_ / ci
    rn = r ** combination['N'][i]
    ploss = rn * (1 - r) / (1 - rn * r)
    return ((1 - ploss) * L_helper(r, combination['N'][i], rn) / ci) + \
           ploss * L_helper(combination['rho0'], combination['N0'], r0n0) / c0


def calculate_metric(slicing, combination):
    numerator = 0
    denominator = 0
    for i in range(slicing.numOfSlices):
        if slicing.slices[i].reqBw:
            numerator = numerator + (B(slicing, combination, i) / slicing.slices[i].reqBw) ** 2
        if slicing.slices[i].reqLat:
            denominator = denominator + (L(slicing, combination, i) / slicing.slices[i].reqLat) ** 2

    numerator = numerator if numerator != 0 else 1
    denominator = denominator if denominator != 0 else 1
    return numerator / denominator


def run_analysis(slicing, combinations, combToMetric):
    for combination in combinations:
        metric = calculate_metric(slicing, combination)
        combToMetric.append([metric, combination])
    return


def checkIfRequirementsPass(slicing, bestComb):
    combination = bestComb[1]
    pp = []
    for i in range(slicing.numOfSlices):
        p = True
        L_ = 0
        B_ = 0
        if slicing.slices[i].reqLat:
            L_ = L(slicing, combination, i)
            if slicing.slices[i].reqLat < L_:
                p = False
        if slicing.slices[i].reqBw:
            B_ = B(slicing, combination, i)
            if slicing.slices[i].reqBw > B_:
                p = False

        if p:
            slicing.slices[i].laesaResult = "LAESA: Passed with best combination: " + str(combination) +\
                                             " which resulted in bandwidth " + str(B_) + " and Latency " + str(L_)
        else:
            slicing.slices[i].laesaResult = "LAESA: Passed with best combination: " + str(combination) +\
                                             " which resulted in bandwidth " + str(B_) + " and Latency " + str(L_)
        pp.append(p)

    return np.prod(pp)


def laesa(slicing):
    possibleN = get_possible_N(slicing)
    CNCombinations = get_possible_CN(slicing, possibleN)

    splitter = int(np.ceil(len(CNCombinations) / NUM_OF_THREADS))

    CNCGroups = []
    for i in range(NUM_OF_THREADS - 1):
        CNCGroups.append(CNCombinations[splitter * i:splitter * (i + 1)])
    CNCGroups.append(CNCombinations[splitter * (NUM_OF_THREADS - 1):])

    threads = []
    combToMetric = []

    for index in range(NUM_OF_THREADS):
        x = threading.Thread(target=run_analysis, args=(slicing, CNCGroups[index], combToMetric,))
        threads.append(x)
        x.start()

    for index in range(NUM_OF_THREADS):
        threads[index].join()

    metricList = list(map(lambda x: x[0], combToMetric))
    bestElement = combToMetric[metricList.index(max(metricList))]

    result = checkIfRequirementsPass(slicing, bestElement)

    return result