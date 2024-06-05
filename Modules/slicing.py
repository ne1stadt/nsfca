import numpy as np
from Modules.haesa1 import haesa1
from Modules.haesa2 import haesa2
from Modules.laesa import laesa

TRAFFIC_TYPE_TO_LAMBDA = {
    "ftp": 1
}

class Station:
    def __init__(self,  numPRBs, PRBbandwidth, buffer):
        self.numPRBs = numPRBs
        self.PRBbandwidth = PRBbandwidth
        self.buffer = buffer
        self.C = self.numPRBs * self.PRBbandwidth

    def describe(self):
        print(str(self.numPRBs) + " number of PRBs with " + str(self.PRBbandwidth) +
              " bandwidth each which makes " + str(self.C) + " total. Buffer Size is " + str(self.buffer) + ".")

class Slice:
    def __init__(self, name, numOfUsers, trType, reqBw = False, reqLat = False):
        self.name = name
        self.numOfUsers = numOfUsers
        self.trType = trType
        self.lambda_ = TRAFFIC_TYPE_TO_LAMBDA[self.trType] * self.numOfUsers
        self.reqBw = reqBw
        self.reqLat = reqLat
        self.haesa1Result = None
        self.haesa2Result = None
        self.laesaResult = None

    def describe(self):
        print("Slice " + self.name + ":")
        print(str(self.numOfUsers) + " users of " + self.trType +
              " traffic type, which results in total equivalent lambda " + str(self.lambda_) + ".")
        if self.reqBw and self.reqLat:
            print("Required Bandwidth for slice is " + str(self.reqBw) +
                  " mbps and Required Latency is " + str(self.reqLat) + " ms.")
        elif self.reqBw:
            print("Required Bandwidth for slice is " + str(self.reqBw) + " mbps.")
        elif self.reqLat:
            print("Required Latency for slice is " + str(self.reqLat) + " ms.")

    def detailed_results(self):
        text = "Slice " + self.name + ": \n"
        if self.haesa1Result != None:
            text = text + self.haesa1Result + "\n"
        if self.haesa2Result != None:
            text = text + self.haesa2Result + "\n"
        if self.laesaResult != None:
            text = text + self.laesaResult + "\n"
        print(text)

class Slicing:
    def __init__(self, station, slices):
        self.station = station
        self.slices = slices
        self.numOfSlices = len(slices)
        self.sumLambda = sum(list(map(lambda x: x.lambda_, self.slices)))
        self.N = int(np.floor(self.station.buffer / self.sumLambda))

    def describe(self):
        print("Slicing on Base station: ")
        self.station.describe()
        print("\nWith slices:")
        for slice in self.slices:
            slice.describe()
        print("That makes total lambda " + str(self.sumLambda) +
              " and buffer signal size of " + str(self.N) + ".")

    def check_haesa1(self):
        return haesa1(self)

    def check_haesa2(self):
        return haesa2(self)

    def check_laesa(self):
        return laesa(self)

    def detailed_results(self):
        for slice in self.slices:
            slice.detailed_results()
        return

def read_slicing(file):
    base = Station(file["numPRBs"], file["PRBbandwidth"], file["buffer"])
    slices = []
    for slice in file["slices"]:
        slices.append(Slice(slice["name"],
                            slice["numOfUsers"],
                            slice["trType"],
                            slice["reqBw"] if "reqBw" in slice.keys() else False,
                            slice["reqLat"] if "reqLat" in slice.keys() else False))
    return Slicing(base, slices)