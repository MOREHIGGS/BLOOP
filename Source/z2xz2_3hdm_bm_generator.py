import math as m
import numpy as np
import pdg
from scipy.constants import physical_constants as constants
import json
from pathlib import Path
from os.path import join
from glob import glob
from copy import copy
from tqdm import tqdm
from matplotlib import pyplot as plt
from track_vev import cNlopt

api = pdg.connect()
mHiggs = api.get_particle_by_name("H").mass
mTop = api.get_particle_by_name("t").mass
mW = api.get_particle_by_name("W+").mass
mZ = api.get_particle_by_name("Z0").mass
higgsVEV = 1/m.sqrt((m.sqrt(2) * constants["Fermi coupling constant"][0]))

def generateBenchmarks(args):
    if args.benchmarkType == "load":
        return 
     
    moduleDirectory = Path(__file__).resolve().parent/"../Build"/args.modelDirectory 
    (outputFilePath := Path(moduleDirectory/args.benchmarkFilePath)).parent.mkdir(exist_ok=True, parents=True)
    
    bmdictList = []
    
    if args.benchmarkType == "venusBms":
        bmGenerator = venusBms("A")     

    if args.benchmarkType == "testDim6":
        bmGenerator = testDim6()     

    elif args.benchmarkType == "loadDDSafe":
        bmGenerator = loadDDSafe(args.previousResultDirectory)     

    elif args.benchmarkType == "subSetDark":
        bmGenerator = subSetDark(args.previousResultDirectory)     
    
    elif args.benchmarkType == "strongSubSet":
        bmGenerator = strongSubSet(args.previousResultDirectory)     
 
    elif args.benchmarkType == "increasedeltas":
        bmGenerator = increasedeltas(args.previousResultDirectory)     
    
    elif args.benchmarkType == "franBms":
        bmGenerator = franBms()     

    elif args.benchmarkType == "fixLamdaBms":
        bmGenerator = fixLamdaBms(args.benchmarkSubType)     

    elif args.benchmarkType == "checkDecouplingDelta":
        bmGenerator = checkDecouplingDelta()     


    else:
        print(f"{args.benchmarkType} isn't recongised as an option, exiting")
        exit()
   
    unBoundedList = []    
    wrongVEVList = []
    passedList = []
    with tqdm(total=args.numBenchmarks, desc="Generating benchmarks", unit="bm") as pbar:
        for bmParams in bmGenerator:
            if len(bmdictList) == args.numBenchmarks:
                break
            if bmParams:
                ## copy is needed otherwise the background fields enter the 4D beta function
                ## and lead to small numerical errors (~1e-3%) in the couplings
                ## This error is of order the tol of solve_ivp so maybe not important? 
                physicalStatus = checkPhysical(copy(bmParams["lagranianParameters"]))
                if physicalStatus == "unbounded":
                    unBoundedList.append(list(bmParams["bmInput"].values()))
                
                if physicalStatus == "wrongVEV":
                    wrongVEVList.append(list(bmParams["bmInput"].values()))
                
                else:
                    passedList.append(list(bmParams["bmInput"].values()))
                    bmParams["bmNumber"] = len(bmdictList)
                    bmdictList.append(bmParams)
                    pbar.update(1)
     
    passedList = np.transpose(passedList)
    print("passed")
    print(passedList.shape)
    wrongVEVList = np.transpose(wrongVEVList)
    print("wrongVEV")
    print(wrongVEVList.shape)
    unBoundedList = np.transpose(unBoundedList)
    print("unbounded")
    print(unBoundedList.shape)
    allData = [passedList]
    dataName = ["passed"]
    if len(wrongVEVList) > 0:
        allData.append(wrongVEVList)
        dataName.append("wrongVEVList")
    if len(unBoundedList) >0:
        allData.append(unBoundedList)
        dataName.append("unBoundedList")
        
    resultsDir = Path(__file__).resolve().parent/f"../Run/{args.resultsDirectory}"
    
    yAxisIndices = (6, 7, 8)
    for LamIdx, yIdx in enumerate(yAxisIndices):
        for nameIdx, data in enumerate(allData):
            plt.scatter(data[0], data[yIdx], s=2**2)
            plt.xlabel("mh1", labelpad=5, fontsize=12)
            plt.ylabel(f"Lambda{LamIdx+1}", labelpad=5, fontsize=12)
            plt.ylim(0.1, 3)
            plt.xlim(40, 105)
            plt.title(f"{dataName[nameIdx]}")
            plt.savefig(resultsDir/f"Lambda{LamIdx+1}_0T_{dataName[nameIdx]}")
            plt.close()
    
    with open(outputFilePath, "w") as fp:        
        json.dump(
            bmdictList,
            fp,
            indent=4,
        )
    return

def strongSubSet(filename):
    with open(filename, "r") as file:
       datas = json.load(file)
    TcMin = 999
    for x in datas:
        if not x["failureReason"] and x["strong"]:
            for y in x["PTData"]:
                TcMin = y["Tc"] if (y["Tc"]<TcMin and not y["EFTBreak"]) else TcMin
    print(TcMin) 
    for data in datas:
        if not data["failureReason"] and data["strong"]:
            yield _lagranianParamGen(
                *data["bmInput"].values()
            )

def loadDDSafe(filename):
    #import json
    #with open(filename, "r") as file:
    #   datas = json.load(file)#.readlines()
    with open(filename, "r") as file:
       datas = file.readlines()
    datas = [data.split()[:13] for data in datas[2:] if data.split()[13] =="1"]
    datas= np.asarray(datas, dtype=np.float64)
    
    for data in datas:
        yield _lagranianParamGen(
         *data
    )

def subSetDark(filename):
    with open(filename, "r") as file:
        results = json.load(file)
    
    change = 1.5
    count = 0
    for result in results:
        if not result["failureReason"] and result["strong"]:

            bmInput = result["bmInput"]
            #bmInput["$\\lambda_{12}$"] *= change
            #bmInput["$\\lambda'_{12}$"] *= change
            #bmInput["$\\lambda_{11}$"] *= change
            bmInput["$\\lambda_{22}$"] *= change
            count+=1
            a = [val for val in bmInput.values()]
            yield _lagranianParamGen(
             *a
        )


def increasedeltas(filename):
    with open(filename, "r") as file:
        results = json.load(file)
    
    change = 1.5
    for result in results:
        if not result["failureReason"] and result["strong"]:

            bmInput = result["bmInput"]
            #bmInput["$m_{a_{1}}$"] *= change
            bmInput["$m_{h^\pm_{1}}$"] *= change
            #a = [val for val in bmInput.values()]
            yield _lagranianParamGen(
             *[val for val in bmInput.values()]
        )

def testDim6():
    
    for x in range(10, 300,10):
        mh1 = 60 + x
        ma1 = 65 + x
        mh1p = 70 + x
        mh2 = 80 + x
        ma2 = 85 + x
        mh2p = 90 + x
        lamda11 = 1.3
        lamda22 = 1.2
        lamda12 = 0.13
        lamda12p = 0.14
        lamda1 = 0.1
        lamda2 = 0.8
        lamda3 = 0.9
        yield _lagranianParamGen(
             mh1,ma1, mh1p, mh2, ma2, mh2p, lamda1, lamda2, lamda3, lamda11, lamda22, lamda12, lamda12p
        )
    




def venusBms(bmType, seed = None):
    bmTypes = {
        "A": {"mh1Min": 46, "mh1Max": 100, "Delta": 80, "deltaa1": 100, "deltaa2": 100, "deltac1": 105, "deltac2": 105},
        "B": {"mh1Min": 46, "mh1Max": 100, "Delta": 5, "deltaa1": 100, "deltaa2": 100, "deltac1": 105, "deltac2": 105},
        "C": {"mh1Min": 46, "mh1Max": 100, "Delta": 100, "deltaa1": 5, "deltaa2": 5, "deltac1": 90, "deltac2": 10},
        "D": {"mh1Min": 46, "mh1Max": 100, "Delta": 5, "deltaa1": 10, "deltaa2": 10, "deltac1": 100, "deltac2": 100},
        "E": {"mh1Min": 80, "mh1Max": 150, "Delta": 100, "deltaa1": 90, "deltaa2": 15, "deltac1": 10, "deltac2": 10},
        "F15": {"mh1Min": 80, "mh1Max": 150, "Delta": 5, "deltaa1": 90, "deltaa2": 100, "deltac1": 10, "deltac2": 15},
        "F95": {"mh1Min": 80, "mh1Max": 150, "Delta": 5, "deltaa1": 90, "deltaa2": 100, "deltac1": 10, "deltac2": 95},
        "G": {"mh1Min": 80, "mh1Max": 150, "Delta": 80, "deltaa1": 5, "deltaa2": 5, "deltac1": 10, "deltac2": 10},
        "H10": {"mh1Min": 80, "mh1Max": 150, "Delta": 5, "deltaa1": 5, "deltaa2": 5, "deltac1": 10, "deltac2": 10},
        "H95": {"mh1Min": 80, "mh1Max": 150, "Delta": 5, "deltaa1": 5, "deltaa2": 5, "deltac1": 10, "deltac2": 95},
        "beta45": {"mh1Min": 46, "mh1Max": 100, "Delta": 45, "deltaa1": 100, "deltaa2": 60, "deltac1": 105, "deltac2": 65},
        "beta20m0p": {"mh1Min": 46, "mh1Max": 100, "Delta": 5, "deltaa1": 80, "deltaa2": 80, "deltac1": 105, "deltac2": 105},
        "beta20p0p": {"mh1Min": 46, "mh1Max": 100, "Delta": 5, "deltaa1": 120, "deltaa2": 120, "deltac1": 105, "deltac2": 105},
        "beta0p20m": {"mh1Min": 46, "mh1Max": 100, "Delta": 5, "deltaa1": 100, "deltaa2": 100, "deltac1": 85, "deltac2": 85},
        "beta0p20p": {"mh1Min": 46, "mh1Max": 100, "Delta": 5, "deltaa1": 100, "deltaa2": 100, "deltac1": 125, "deltac2": 125},
    }
    data = bmTypes[bmType]
    vsq = higgsVEV**2
    mu3Sq = mHiggs**2 / 2
    lamda33 = mu3Sq / vsq
    
    if True:
        np.random.seed(1)

    while True:
        mh1 = np.random.uniform(data["mh1Min"], data["mh1Max"])
        ma1 = mh1 + data["deltaa1"]
        mh1p = mh1 + data["deltac1"]
        mh2 = mh1 + data["Delta"]
        ma2 = mh2 + data["deltaa2"]
        mh2p = mh2 + data["deltac2"] 
        lamda11 = 0.1
        lamda22 = 0.12
        lamda12 = 0.13
        lamda12p = 0.14
        Lamda1 = np.random.uniform(-0.2, 0.2)
        Lamda2 = np.random.uniform(-0.2, 0.2)
        Lamda3 = np.random.uniform(-0.2, 0.2)
        yield _lagranianParamGen(
             mh1,ma1, mh1p, mh2, ma2, mh2p, Lamda1, Lamda2, Lamda3, lamda11, lamda22, lamda12, lamda12p
        )

def fixLamdaBms(bmType):
    bmTypes = {
        "A": {"Lamda2": 0.05, "Lamda3": 0.05},
        "B": {"Lamda2": 0.05, "Lamda3": 0.1},
        "C": {"Lamda2": 0.05, "Lamda3": 0.15},
        "D": {"Lamda2": 0.1, "Lamda3": 0.05},
        "E": {"Lamda2": 0.1, "Lamda3": 0.1},
        "F": {"Lamda2": 0.1, "Lamda3": 0.15},
        "G": {"Lamda2": 0.15, "Lamda3": 0.05},
        "H": {"Lamda2": 0.15, "Lamda3": 0.1},
        "I": {"Lamda2": 0.15, "Lamda3": 0.15},
    }
    data = bmTypes[bmType]
    vsq = higgsVEV**2
    mu3Sq = mHiggs**2 / 2
    lamda33 = mu3Sq / vsq

    while True:
        mh1 = np.random.uniform(46, 100)
        ma1 = mh1 + np.random.uniform(5,100)
        mh1p = ma1 + 5 
        mh2 = mh1 +  np.random.uniform(5, 50)
        ma2 = mh2 + np.random.uniform(5,100)
        mh2p = ma2 + 5 
        lamda11 = 0.1
        lamda22 = 0.12
        lamda12 = 0.13
        lamda12p = 0.14
        Lamda1 = 0.1
        Lamda2 = data["Lamda2"] 
        Lamda3 = data["Lamda3"] 
        yield _lagranianParamGen(
             mh1,ma1, mh1p, mh2, ma2, mh2p, Lamda1, Lamda2, Lamda3, lamda11, lamda22, lamda12, lamda12p
        )

def _lagranianParamGen(
    mh1,ma1, mh1p, mh2, ma2, mh2p, Lamda1, Lamda2, Lamda3, lamda11, lamda22, lamda12, lamda12p
):
    
    mh1Sq = mh1**2
    ma1Sq = ma1**2
    mh1pSq =  mh1p**2
    mh2Sq = mh2**2 
    ma2Sq = ma2**2
    mh2pSq = mh2p**2

    vsq = higgsVEV**2
    mu3Sq = mHiggs**2 / 2
    lamda33 = mu3Sq / vsq
    

    mu1Sq = -mh1Sq + Lamda3*vsq
    lamda3 = (mh1Sq - ma1Sq)/(2*vsq)
    lamda31p = (mh1Sq + ma1Sq - 2*mh1pSq)/vsq
    lamda31 = 2*Lamda3 - 2*lamda3 - lamda31p


    mu2Sq = -mh2Sq + Lamda2*vsq
    lamda2 = (mh2Sq - ma2Sq)/(2*vsq)
    lamda23p = (mh2Sq + ma2Sq - 2*mh2pSq)/vsq
    lamda23 = 2*Lamda2 - 2*lamda2 - lamda23p
    lamda1 = Lamda1 - (lamda12 + lamda12p)*0.5
    
    return {"bmInput": {
                r"$m_{h_{1}}$": mh1,
                r"$m_{a_{1}}$": ma1,
                r"$m_{h^\pm_{1}}$": mh1p,
                r"$m_{h_{2}}$": mh2,
                r"$m_{a_{2}}$": ma2,
                r"$m_{h^\pm_{2}}$": mh2p,
                r"$\Lambda_1$":Lamda1,
                r"$\Lambda_2$":Lamda2,
                r"$\Lambda_3$":Lamda3,
                r"$\lambda_{11}$":lamda11,
                r"$\lambda_{22}$":lamda22,
                r"$\lambda_{12}$":lamda12,
                r"$\lambda'_{12}$":lamda12p,

            },
            "lagranianParameters": {
                "lamda1Re": lamda1,
                "lamda1Im": 0,
                "lamda2Re": lamda2,
                "lamda2Im": 0,
                "lamda11": lamda11,
                "lamda22": lamda22,
                "lamda12": lamda12,
                "lamda12p": lamda12p,
                "lamda23": lamda23,
                "lamda23p": lamda23p,
                "lamda3Re": lamda3,
                "lamda3Im": 0,
                "lamda31": lamda31,
                "lamda31p": lamda31p,
                "lamda33": lamda33,
                "mu3sq": mu3Sq,
                "mu2sq": mu2Sq,
                "mu1sq": mu1Sq,
                "yt3": m.sqrt(2.0) * mTop / higgsVEV,
                "g1": 2.0 * m.sqrt(mZ**2 - mW**2) / higgsVEV,  ## U(1)
                "g2": 2.0 * mW / higgsVEV,  ## SU(2)
                "g3": m.sqrt(0.1183 * 4.0 * np.pi),  ## SU(3)
                "RGScale": 91.1876,
            },
    }


def checkPhysical(params):
    params["v1"] = 0
    params["v2"] = 0
    params["v3"] = 1/m.sqrt((m.sqrt(2) * constants["Fermi coupling constant"][0]))
    if not bIsBounded(params):
        return "unbounded"
    if not bPhysicalMinimum(params):
        return "wrongVEV"
    return ""


def bPhysicalMinimum(params):
    minimumInitialGuesses = [
        [0, 0, 0],
        [0, 0, 250],
        [990, 990, 990],
        [50, 50, 50],
        [500, 500, 500],
    ]
    nloptInst = cNlopt(
        config={
            "nbrVars": 3,
            "absGlobalTol": 0.3,
            "relGlobalTol": 0.3,
            "absLocalTol": 0.005,
            "relLocalTol": 0.005,
            "varLowerBounds": [0, 0, 0],
            "varUpperBounds": [1000, 1000, 1000],
        }
    )
    
    def potential(fields, grad):
        v1, v2, v3 = fields
        return (v1**4*params["lamda11"] + v2**4*params["lamda22"] + v3**4*params["lamda33"] 
                + v1**2*(v2**2*(params["lamda12"] + params["lamda12p"] + 2*params["lamda1Re"]) 
                        + v3**2*(params["lamda31"] + params["lamda31p"] + 2*params["lamda3Re"]) 
                        - 2*params["mu1sq"]) 
                + v2**2*(v3**2*(params["lamda23"] + params["lamda23p"] + 2*params["lamda2Re"]) 
                        - 2*params["mu2sq"]) 
                - 2*v3**2*params["mu3sq"])/4

    minLocation, minValue, a = nloptInst.nloptGlobal(potential, minimumInitialGuesses[0])
    for guess in minimumInitialGuesses:
        minLocationTemp, minValueTemp, a = nloptInst.nloptLocal(potential, guess)
        if minValueTemp < minValue:
            minLocation, minValue = minLocationTemp, minValueTemp

    return np.all(np.isclose(minLocation, [0, 0, higgsVEV], atol=1))

def bIsBounded(params):
    ## Taking equations 26-31 from the draft that ensure the potential is bounded from below.
    
    if params["lamda11"] < 0:
        return False
    if params["lamda22"] < 0:
        return False
    if params["lamda33"] < 0:
        return False

    lamdax = params["lamda12"] + min(
        0, params["lamda12p"] - 2 * abs(params["lamda1Re"])
    )
    lamday = params["lamda31"] + min(
        0, params["lamda31p"] - 2 * abs(params["lamda3Re"])
    )
    lamdaz = params["lamda23"] + min(
        0, params["lamda23p"] - 2 * abs(params["lamda2Re"])
    )
    
    if lamdax < -2 * m.sqrt(params["lamda11"] * params["lamda22"]):
        return False
    
    if lamday < -2 * m.sqrt(params["lamda11"] * params["lamda33"]):
        return False
    if lamdaz < -2 * m.sqrt(params["lamda22"] * params["lamda33"]):
        return False
    
    if not (
        m.sqrt(params["lamda33"]) * lamdax
        + m.sqrt(params["lamda11"]) * lamdaz
        + m.sqrt(params["lamda22"]) * lamday
        >= 0
        or params["lamda33"] * lamdax**2
        + params["lamda11"] * lamdaz**2
        + params["lamda22"] * lamday**2
        - params["lamda11"] * params["lamda22"] * params["lamda33"]
        - 2 * lamdax * lamday * lamdaz
        < 0
    ):
        return False
    return True

