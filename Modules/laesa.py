import threading
import numpy as np
import itertools

NUM_OF_THREADS = 8
STEP = 10

def get_possible_N(slicing):
    iterables = [range(0, slicing.N, STEP)] * (slicing.numOfSlices + 1)
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

    fullCombinations = []
    for a in cCombinations:
        for b in possibleN:
            fullCombinations.append({'cn': a, 'N': b['N'], 'N0': b['N0']})

    print("Number of raw C-N combinations: " + str(len(fullCombinations)))
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
    #return (slicing.slices[i].lambda_ / (1 - rn * r)) * \
    #       (1 - rn * (1 - ((1 - r) * (1 - r0n0) / (1 - r0n0 * combination['rho0']))))
    return (combination['cn'][i] * slicing.station.PRBbandwidth / (1 - rn * r)) * \
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
    return (((1 - ploss) * L_helper(r, combination['N'][i], rn) / ci) + \
           ploss * L_helper(combination['rho0'], combination['N0'], r0n0) / c0) * 1000


def calculate_metric(slicing, combination):
    numerator = 0
    denominator = 0
    passed = True
    Barr = []
    Larr = []
    for i in range(slicing.numOfSlices):
        B_ = B(slicing, combination, i)
        L_ = L(slicing, combination, i)
        if slicing.slices[i].reqBw:
            numerator = numerator + (B_ / slicing.slices[i].reqBw) ** 2
            passed = passed if B_ >= slicing.slices[i].reqBw else False
        if slicing.slices[i].reqLat:
            denominator = denominator + (L_ / slicing.slices[i].reqLat) ** 2
            passed = passed if L_ <= slicing.slices[i].reqLat else False
        Barr.append(B_)
        Larr.append(L_)

    numerator = numerator if numerator != 0 else 1
    denominator = denominator if denominator != 0 else 1
    return {'S': numerator / denominator, 'B': Barr, 'L': Larr, 'passed': passed}


def run_analysis(slicing, combinations, combToMetric):
    for combination in combinations:
        metric = calculate_metric(slicing, combination)
        combToMetric.append([metric, combination])
        #[
        #    {'S': 1, 'B': 2, 'L': 3, 'passed': True},
        #    {'cn': [45, 45, 45], 'N': [5, 5, 5], 'rho0': 1, 'N0': 6}
        #]
    return


def find_best_combination(combToMetric):
    passedCombinations = [x for x in list(map(lambda x: x if x[0]['passed'] else None, combToMetric)) if x is not None]
    if len(passedCombinations) == 0:
        result = False
        metricList = list(map(lambda x: x[0]['S'], combToMetric))
        bestCombination = combToMetric[metricList.index(max(metricList))]
    else:
        result = True
        metricList = list(map(lambda x: x[0]['S'], passedCombinations))
        bestCombination = passedCombinations[metricList.index(max(metricList))]
    return result, bestCombination


def laesa(slicing):
    possibleN = get_possible_N(slicing)
    print("Number of N combinations: " + str(len(possibleN)))
    CNCombinations = get_possible_CN(slicing, possibleN)
    print("Number of C-N combinations: " + str(len(CNCombinations)))

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

    result, bestElement = find_best_combination(combToMetric)

    for i in range(slicing.numOfSlices):
        slicing.slices[i].laesaResult = 'LAESA: Best configuration is ' + str(bestElement[1]['cn'][i]) + \
                                        ' allocated PRBs (rho = ' + \
                                        str(round(slicing.slices[i].lambda_/(bestElement[1]['cn'][i]*slicing.station.PRBbandwidth),2)) + \
                                        ') and N = ' + str(bestElement[1]['N'][i]) + '/' + str(slicing.N) + \
                                        ' which gives B = ' + str(round(bestElement[0]['B'][i], 2)) + \
                                        ' mbps and L = ' + str(round(bestElement[0]['L'][i], 2)) + ' ms'

    return result