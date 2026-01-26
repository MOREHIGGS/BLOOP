"""Generate benchmarks at 0T satisfying some constraints."""

import math as m
import numpy as np
import pdg
from scipy.constants import physical_constants as constants
import json
from pathlib import Path
from os.path import join
from glob import glob
from copy import copy

from ParsedExpression import ParsedExpression
from TrackVEV import cNlopt

def generateBenchmarks(args):
    if args.benchmarkType == "load":
        return 
    
    nloptInst = cNlopt(
        config={
            "nbrVars": 3,
            "absGlobalTol": 0.5,
            "relGlobalTol": 0.5,
            "absLocalTol": 0.5,
            "relLocalTol": 0.5,
            "varLowerBounds": [-300, 0, 0],
            "varUpperBounds": [300, 300, 300],
        }
    )
    
    with open(args.pythonisedExpressionsFilePath, "r") as fp:
        parsedExpressions = json.load(fp)
    chargedMassMatrix = ParsedExpression(
        parsedExpressions["scalarMassMatrices"]["expressions"][0], None
    )
    neutralMassMatrix = ParsedExpression(
        parsedExpressions["scalarMassMatrices"]["expressions"][1], None
    )

    (outputFilePath := Path(args.benchmarkFilePath)).parent.mkdir(exist_ok=True, parents=True)
    
    if args.benchmarkType == "randomSSS":
        with open(outputFilePath, "w") as fp:
            json.dump(strongSubSet(args.prevResultDir), fp, indent=4)
        return
    
    bmdictList = []
    
    if args.benchmarkType == "handPicked":
        bmGenerator = handPickedParameters()
        
    elif args.benchmarkType == "random":
        bmGenerator = randomParameters()     
    
    for bmParams in bmGenerator:
        if len(bmdictList) == args.maxNumBenchmarks:
            break
        if bmParams:
            ### IMPORTANT ###
            ## copy is needed otherwise the background fields enter the 4D beta function
            ## and lead to small numerical errors (~1e-3%) in the couplings
            ## Note: The error is of order the tol of solve_ivp so maybe not important? 
                if checkPhysical(
                    copy(bmParams["lagranianParameters"]),
                    nloptInst,
                    chargedMassMatrix,
                    neutralMassMatrix,
                ):
                    bmParams["bmNumber"] = len(bmdictList)
                    bmdictList.append(bmParams)
    
    with open(outputFilePath, "w") as fp:        
        json.dump(
            bmdictList,
            fp,
            indent=4,
        )
    return



def handPickedParameters():
    bmInputList = [
        ##Strong
        [99.36450394464288, 42.80075856374667, 96.06869518984769, 5.2678728361278155, 0.5086042817226999, 2.5522714805947393, 1],
        ##Weak
        [67, 4.0, 50.0, 1.0, 0.0, 2.0 * np.pi / 3, 1],
        ##2 step complex
        [68.43630541987292,  79.0888560988479, 45.64676671775482, 27.279729519388148, 0.5364316612973308, 3.082183112574816, 1],
        ##2 step real
        [69.13440475054537, 62.67361616764857, 89.67096039014373, 19.87132366433007, 0.49693161396025076, 1.893580908713017, 1],
        [70, 12.0, 50.0, 1.0, 0.0, 2.0 * np.pi / 3, 1],
        [75, 55.0, 50.0, 1.0, 0.0, 2.0 * np.pi / 3, 1],
        [74, 55.0, 50.0, 15.0, 0.0, 2.0 * np.pi / 3, 1],
        [90, 5.0, 1.0, 1.0, 0.0, 2.0 * np.pi / 3, 1],
        [90, 55.0, 1.0, 22.0, 0.0, 2.0 * np.pi / 3, 1],
    ]

    for bmInput in bmInputList:
        yield _lagranianParamGen(*bmInput)


def randomParameters():
    while True:
        mS1 = np.random.uniform(63, 100)
        delta12 = np.random.uniform(5, 100)
        delta1c = np.random.uniform(5, 100)
        deltac = np.random.uniform(5, 100)
        ghDM = np.random.uniform(0, 1)
        thetaCPV = np.random.uniform(np.pi / 2, 3 * np.pi / 2)
        yield _lagranianParamGen(
            mS1, delta12, delta1c, deltac, ghDM, thetaCPV, 1
        )


def strongSubSet(prevResultDir):
    bmdictList = []

    for fileName in glob(join(prevResultDir, "*.json")):
        with open(fileName, "r") as fp:
            resultDic = json.load(fp)

        if resultDic["strong"]:
            bmdictList.append(
                _lagranianParamGen(
                    resultDic["bmInput"]["mS1"],
                    resultDic["bmInput"]["delta12"],
                    resultDic["bmInput"]["delta1c"],
                    resultDic["bmInput"]["deltac"],
                    resultDic["bmInput"]["ghDM"],
                    resultDic["bmInput"]["thetaCPV"],
                    resultDic["bmInput"]["darkHieracy"],
                    resultDic["bmNumber"],
                )
            )

    return bmdictList


def _lagranianParamGen(
    mS1, delta12, delta1c, deltac, ghDM, thetaCPV, darkHieracy
):
    api = pdg.connect()
    mHiggs = api.get_particle_by_name("H").mass
    mTop = api.get_particle_by_name("t").mass
    mW = api.get_particle_by_name("W+").mass
    mZ = api.get_particle_by_name("Z0").mass

    higgsVEV = 1/m.sqrt((m.sqrt(2) * constants["Fermi coupling constant"][0]))

    vsq = higgsVEV**2
    mu3sq = mHiggs**2 / 2
    lamda33 = mu3sq / vsq

    mS2 = delta12 + mS1
    mSpm1 = delta1c + mS1
    mSpm2 = deltac + mSpm1
    mu12sq = (mSpm2**2 - mSpm1**2) / 2

    sinTheta, cosTheta = m.sin(thetaCPV), m.cos(thetaCPV)
    lamda2absInsideSqR = (
        (2.0 * mu12sq * cosTheta) ** 2
        + (mS2**2 - mS1**2) ** 2
        - (mSpm2**2 - mSpm1**2) ** 2
    )
    if lamda2absInsideSqR < 0:
        return False

    lamda2Abs = (mu12sq * cosTheta + m.sqrt(lamda2absInsideSqR) / 4) / vsq
    lamda2Re = lamda2Abs * cosTheta
    lamda2Im = lamda2Abs * sinTheta

    alpha = (
        -mu12sq
        + vsq * lamda2Abs * cosTheta
        - m.sqrt(
            mu12sq**2 + vsq**2 * lamda2Abs**2 - 2.0 * vsq * mu12sq * lamda2Abs * cosTheta
        )
    ) / ((vsq * lamda2Abs * sinTheta) + 1e-100)
    mu2sq = (
        vsq / 2.0 * ghDM
        - vsq
        / (alpha**2 + 1.0)
        * (2.0 * alpha * sinTheta + (alpha**2 - 1.0) * cosTheta)
        * lamda2Abs
        - (mS2**2 + mS1**2) / 2
    )
    lamda23 = (2.0 * mu2sq + mSpm2**2 + mSpm1**2) / vsq
    lamda23p = (mS2**2 + mS1**2 - mSpm2**2 - mSpm1**2) / vsq

    return {
        "bmInput": {
            "thetaCPV": thetaCPV,
            "ghDM": ghDM,
            "mS1": mS1,
            "delta12": delta12,
            "delta1c": delta1c,
            "deltac": deltac,
            "darkHieracy": darkHieracy,
        },
        "lagranianParameters": {
            "lamda1Re": 0.1,
            "lamda1Im": 0,
            "lamda2Re": lamda2Abs * cosTheta,
            "lamda2Im": lamda2Abs * sinTheta,
            "lamda11": 0.11,
            "lamda22": 0.12,
            "lamda12": 0.13,
            "lamda12p": 0.14,
            "lamda23": lamda23,
            "lamda23p": lamda23p,
            "lamda3Re": darkHieracy * lamda2Re,
            "lamda3Im": darkHieracy * lamda2Im,
            "lamda31": darkHieracy * lamda23,
            "lamda31p": darkHieracy * lamda23p,
            "lamda33": lamda33,
            "mu12sqRe": mu12sq,
            "mu12sqIm": 0,
            "mu2sq": mu2sq,
            "mu3sq": mu3sq,
            "mu1sq": darkHieracy * mu2sq,
            "yt3": m.sqrt(2.0) * mTop / higgsVEV,
            "g1": 2.0 * m.sqrt(mZ**2 - mW**2) / higgsVEV,  ## U(1)
            "g2": 2.0 * mW / higgsVEV,  ## SU(2)
            "g3": m.sqrt(0.1183 * 4.0 * np.pi),  ## SU(3)
            "RGScale": 91.1876,
        },
    }


def checkPhysical(params, nloptInst, chargedMassMatrix, neutralMassMatrix):
    params["v1"] = 0
    params["v2"] = 0
    params["v3"] = 1/m.sqrt((m.sqrt(2) * constants["Fermi coupling constant"][0]))
    if not bIsBounded(params):
        return False

    chargedEigenValues = np.linalg.eigvalsh(chargedMassMatrix.evaluate(params))
    ## Enforces positive charged masses (tolerance to handle goldstone bosons)
    if not np.all(chargedEigenValues >= -1e-20):
        return False
    ## ASSUMING ONLY TWO GOLDSTONES check if masses are heavy enough to avoid dection
    if not np.all(chargedEigenValues[2:] >= 8100):
        return False

    neutralEigenValues = np.linalg.eigvalsh(neutralMassMatrix.evaluate(params))
    ## Enforces positive neutral masses
    if not np.all(neutralEigenValues >= -1e-20):
        return False
    ## ASSUMING ONLY ONE GOLDSTONE check if masses are heavy enough to avoid
    ## Higgs decaying to light particle
    if not np.all(neutralEigenValues[1:] >= 3969):
        return False

    if not bPhysicalMinimum(nloptInst, params):
        return False

    return True

def bPhysicalMinimum(nloptInst, params):
    minimumInitialGuesses = [
        [0, 0, 0],
        [0, 0, 246],
        [100, 100, 100],
        [-100, 100, 100],
        [50, 50, 50],
        [299, 299, 299],
        [-299, 299, 299],
    ]

    def potential(fields, _):
        v1 = fields[0]
        v2 = fields[1]
        v3 = fields[2]
        return (v1**4*params["lamda11"] + v2**4*params["lamda22"] + v3**4*params["lamda33"] 
                + v1**2*(v2**2*(params["lamda12"] + params["lamda12p"] + 2*params["lamda1Re"]) 
                        + v3**2*(params["lamda31"] + params["lamda31p"] + 2*params["lamda3Re"]) 
                        - 2*params["mu1sq"]) 
                + v2**2*(v3**2*(params["lamda23"] + params["lamda23p"] + 2*params["lamda2Re"]) 
                        - 2*params["mu2sq"]) 
                - 4*v1*v2*params["mu12sqRe"] - 2*v3**2*params["mu3sq"])/4

    
    minLocation, minValue = nloptInst.nloptGlobal(potential, minimumInitialGuesses[0])

    for guess in minimumInitialGuesses:
        minLocationTemp, minValueTemp = nloptInst.nloptLocal(potential, guess)

        if minValueTemp < minValue:
            minLocation, minValue = minLocationTemp, minValueTemp
    higgsVEV = 1/m.sqrt((m.sqrt(2) * constants["Fermi coupling constant"][0]))
    return np.all(np.isclose(minLocation, [0, 0, higgsVEV], atol=1))

def bIsBounded(params):
    ## Taking equations 26-31 from the draft that ensure the potential is bounded from below.
    if not params["lamda11"] > 0:
        return False
    if not params["lamda22"] > 0:
        return False
    if not params["lamda33"] > 0:
        return False

    lamdax = params["lamda12"] + min(
        0, params["lamda12p"] - 2 * m.sqrt(params["lamda1Re"] ** 2 + params["lamda1Im"] ** 2)
    )
    lamday = params["lamda31"] + min(
        0, params["lamda31p"] - 2 * m.sqrt(params["lamda3Re"] ** 2 + params["lamda3Im"] ** 2)
    )
    lamdaz = params["lamda23"] + min(
        0, params["lamda23p"] - 2 * m.sqrt(params["lamda2Re"] ** 2 + params["lamda2Im"] ** 2)
    )
    if not lamdax > -2 * m.sqrt(params["lamda11"] * params["lamda22"]):
        return False
    if not lamday > -2 * m.sqrt(params["lamda11"] * params["lamda33"]):
        return False
    if not lamdaz > -2 * m.sqrt(params["lamda22"] * params["lamda33"]):
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


from unittest import TestCase


class BmGeneratorUnitTests(TestCase):
    maxDiff=None
    def test_bIsBoundedFalse(self):
        source = {
            "mu12sqRe": 12724.595168103033,
            "mu12sqIm": 0,
            "mu2sq": -20604.175986862854,
            "mu3sq": 7812.5,
            "mu1sq": -20604.175986862854,
            "lamda1Re": 0.1,
            "lamda1Im": 0.0,
            "lamda2Re": 0.08368703688875163,
            "lamda2Im": 0.05054893896685599,
            "lamda11": 0.11,
            "lamda22": 0.12,
            "lamda12": 0.13,
            "lamda12p": 0.14,
            "lamda23": 0.13184965469208287,
            "lamda23p": -0.10179114069822925,
            "lamda3Re": 0.08368703688875163,
            "lamda3Im": 0.05054893896685599,
            "lamda31": 0.13184965469208287,
            "lamda31p": -0.10179114069822925,
            "lamda33": 0.12886749199352251,
        }
        self.assertEqual(False, bIsBounded(source))

    def test_bIsBoundedTrue(self):
        source = {
            "mu12sqRe": 4799.941333804141,
            "mu12sqIm": 0,
            "mu2sq": -11505.594825493996,
            "mu3sq": 7812.5,
            "mu1sq": -11505.594825493996,
            "lamda1Re": 0.1,
            "lamda1Im": 0.0,
            "lamda2Re": 0.010823997158779158,
            "lamda2Im": 0.017584425457946057,
            "lamda11": 0.11,
            "lamda22": 0.12,
            "lamda12": 0.13,
            "lamda12p": 0.14,
            "lamda23": 0.33218995023667736,
            "lamda23p": -0.29472720912675215,
            "lamda3Re": 0.010823997158779158,
            "lamda3Im": 0.017584425457946057,
            "lamda31": 0.33218995023667736,
            "lamda31p": -0.29472720912675215,
            "lamda33": 0.12886749199352251,
        }
        self.assertEqual(True, bIsBounded(source))

    def test_lagranianParamGen(self):
        reference = {'bmInput': {'thetaCPV': 3.11308902835221, 'ghDM': 0.15520161865427817, 'mS1': 89.15641588128479, 'delta12': 87.17952518246265, 'delta1c': 14.020273320699415, 'deltac': 5.129099092707543, 'darkHieracy': 1}, 'lagranianParameters': {'lamda1Re': 0.1, 'lamda1Im': 0, 'lamda2Re': -0.08646892283299933, 'lamda2Im': 0.0024653454694036642, 'lamda11': 0.11, 'lamda22': 0.12, 'lamda12': 0.13, 'lamda12p': 0.14, 'lamda23': 0.05327468098550607, 'lamda23p': 0.2749344421058253, 'lamda3Re': -0.08646892283299933, 'lamda3Im': 0.0024653454694036642, 'lamda31': 0.05327468098550607, 'lamda31p': 0.2749344421058253, 'lamda33': 0.12927959478844336, 'mu12sqRe': 542.3572917258725, 'mu12sqIm': 0, 'mu2sq': -9572.921254799061, 'mu3sq': 7837.461207406938, 'mu1sq': -9572.921254799061, 'yt3': 0.9911288650670501, 'g1': 0.3498276219479385, 'g2': 0.6528885874117552, 'g3': 1.2192627459570353,'RGScale': 91.1876}}
        source = (
            89.15641588128479,
            87.17952518246265,
            14.020273320699415,
            5.129099092707543,
            0.15520161865427817,
            3.11308902835221,
            1,
        )
        self.assertEqual(reference, _lagranianParamGen(*source))

    
    def test_HiggsMass(self):
        api = pdg.connect()
        reference = [125.1995304097179, 172.5590883453979, 80.377, 91.18797809193725]
        pdgData = [api.get_particle_by_name("H").mass, api.get_particle_by_name("t").mass, api.get_particle_by_name("W+").mass, api.get_particle_by_name("Z0").mass]
        self.assertEqual(reference,  pdgData, "Data we imported from PDG is not what we expect. Likely just a version difference.")

    def test_Fermi(self):
        self.assertEqual(
            1.1663787e-05, constants["Fermi coupling constant"][0], "Data we imported from Scipy is not what we expect. Likely just a version difference."
        )
