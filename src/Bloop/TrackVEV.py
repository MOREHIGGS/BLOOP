from math import sqrt, pi, log, exp
import numpy as np
import scipy
import nlopt
from dataclasses import dataclass, InitVar, field

from Bloop.PDGData import mTop, mW, mZ, higgsVEV
from .Veff import Veff, eigen

@dataclass(frozen=True)
class cNlopt:
    nbrVars: int = 0
    varLowerBounds: tuple[float] = (0,)
    varUpperBounds: tuple[float] = (0,)
    absLocalTol: float = 0
    relLocalTol: float = 0
    absGlobalTol: float = 0
    relGlobalTol: float = 0
    config: InitVar[dict] = None

    ##Regular init method doesn't work with frozen data classes,
    ##Need to manually init by passing the class a dict i.e. class(config = dict)
    def __post_init__(self, config: dict):
        if config:
            self.__init__(**config)

    def nloptGlobal(self, func: callable, initialGuess: list[float]):
        opt = nlopt.opt(nlopt.GN_DIRECT_NOSCAL, self.nbrVars)
        opt.set_min_objective(func)
        opt.set_lower_bounds(self.varLowerBounds)
        opt.set_upper_bounds(self.varUpperBounds)
        opt.set_xtol_abs(self.absGlobalTol)
        opt.set_xtol_rel(self.relGlobalTol)
        return self.nloptLocal(func, opt.optimize(initialGuess))

    def nloptLocal(self, func: callable, initialGuess: list[float]):
        opt = nlopt.opt(nlopt.LN_BOBYQA, self.nbrVars)
        opt.set_min_objective(func)
        opt.set_lower_bounds(self.varLowerBounds)
        opt.set_upper_bounds(self.varUpperBounds)
        opt.set_xtol_abs(self.absLocalTol)
        opt.set_xtol_rel(self.relLocalTol)
        return opt.optimize(initialGuess), opt.last_optimum_value()


def bIsPerturbative(params, pertSymbols, allSymbols):
    for pertSymbol in pertSymbols:
        if abs(params[allSymbols.index(pertSymbol)]) > 4 * pi:
            return False

    return True

@dataclass(frozen=True)
class TrackVEV:
    TRange: tuple = (0,)
    fieldNames: list = field(default_factory=list)

    pertSymbols: frozenset = frozenset({1})

    initialGuesses: tuple = (0,)

    ## idk how to type hint this correctly
    nloptInst: str = "nloptInstance"
    
    hardToSoft: callable = 0
    softScaleRGE: callable = 0
    softToUltraSoft: callable = 0
    betaFunction4DExpression: str = "betaFunction4DExpression"
    bounded: str = "bounded"

    verbose: bool = False

    EulerGammaPrime = 2.0 * (log(4.0 * pi) - np.euler_gamma)
    Lfconst = 4.0 * log(2.0)

    allSymbols: list = field(default_factory=list)

    config: InitVar[dict] = None

    def __post_init__(self, config):
        if config:
            self.__init__(**config)

    def trackVEV(self, benchmark):
        minimizationResults = {
            "T": [],
            "vevDepthReal": [],
            "vevDepthImag": [],
            "vevLocation": [],
            "bIsPerturbative": [],
            "failureReason": False,
        }

        params = self.getLagranianParams4D(benchmark)

        ## RG running. We want to do 4D -> 3D matching at a scale where logs are small;
        ## usually a T-dependent scale 4.*pi*exp(-np.euler_gamma)*T
        ## TODO FIX for when user RGscale < 7T!!!

        muRange = np.linspace(
            params[self.allSymbols.index("RGScale")],
            7.3 * self.TRange[-1],
            len(self.TRange) * 10,
        )

        ## -----Unexepected behaviour------
        ## This updates the RGScale with the value of mu
        ## including mu in np.real or not gives fp errors
        def betaFunction(
                mu, 
                initialConditions
            ):
                return np.real(self.betaFunction4DExpression.evaluate(initialConditions) / mu)
                
        solvedBetaFunction = scipy.integrate.solve_ivp(
            betaFunction,
            (muRange[0], muRange[-1]),
            params,
            t_eval=muRange
        )
        
        if not solvedBetaFunction.success:
            return minimizationResults | {"failureReason":  solvedBetaFunction.message}
        
        betaSpline4D = {
            symbol: scipy.interpolate.CubicSpline(muRange, solvedBetaFunction.y[idx])
            for idx, symbol in enumerate(self.allSymbols)
            if symbol != "RGScale"
            if np.any(solvedBetaFunction.y[idx] != solvedBetaFunction.y[idx][0])
        }

        counter = 0
        ## Initialise vevLocation to feed into the minimisation algo so it can
        ## use the location of the previous minimum as a guess for the next
        ## Not ideal as the code has to repeat an initial guess on first T
        vevLocation = np.array(self.initialGuesses[0])

        for T in self.TRange:
            if self.verbose:
                print(f"Start of temp = {T} loop")

            params = self.runParams4D(betaSpline4D, T)

            if not np.all(self.bounded.evaluateUnordered(params)):
                return minimizationResults | {"failureReason": "unBounded"}

            isPert = bIsPerturbative(params, self.pertSymbols, self.allSymbols)

            params = self.hardToSoft.evaluate(params)
            params = self.softScaleRGE.evaluate(params)
            params = self.softToUltraSoft.evaluate(params)

            ## Round needed because nlopt result sometimes fp out of bounds
            ## See https://github.com/stevengj/nlopt/issues/625
            vevLocation, vevDepth = self.findGlobalMinimum(
                params, self.initialGuesses + [np.round(vevLocation, 8)]
            )
           
            minimizationResults["T"].append(T)
            minimizationResults["vevDepthReal"].append(vevDepth.real)
            minimizationResults["vevDepthImag"].append(vevDepth.imag)
            minimizationResults["vevLocation"].append(vevLocation)
            minimizationResults["bIsPerturbative"].append(isPert)

            if np.all(np.abs(vevLocation) < 0.5):
                if self.verbose:
                    print(f"Symmetric phase found at temp {T}")

                if counter == 3:
                    break

                counter += 1

        minimizationResults["vevLocation"] = np.transpose(
            minimizationResults["vevLocation"]
        ).tolist()

        return minimizationResults
    
    def findGlobalMinimum(self, params3D, minimumCandidates):
        """For physics reasons we only minimise the real part,
        for nlopt reasons we need to give a redunant grad arg"""
        def VeffWrapper(fields, grad):
            return np.real(
                    self.evaluatePotential(fields, params3D)
                )

        bestResult = self.nloptInst.nloptGlobal(VeffWrapper, minimumCandidates[0])

        for candidate in minimumCandidates:
            result = self.nloptInst.nloptLocal(VeffWrapper, candidate)
            if result[1] < bestResult[1]:
                bestResult = result

        ## Potential computed again in case its complex
        return bestResult[0], self.evaluatePotential(bestResult[0], params3D)
    
    def evaluatePotential(self, fields, params):
        for i, value in enumerate(fields):
            params[self.allSymbols.index(self.fieldNames[i])] = value

        eigen(params)

        return sum(Veff(*params))

    def getLagranianParams4D(self, paramsDict):
        ## --- SM fermion and gauge boson masses---
        ## How get g3 from PDG??
        paramsDict = {
            "yt3": sqrt(2.0) * mTop / higgsVEV,
            "g1": 2.0 * sqrt(mZ**2 - mW**2) / higgsVEV,  ## U(1)
            "g2": 2.0 * mW / higgsVEV,  ## SU(2)
            "g3": sqrt(0.1183 * 4.0 * pi),  ## SU(3)

            ## BSM stuff from benchmark
            "RGScale": paramsDict["RGScale"],
            **paramsDict["massTerms"],
            **paramsDict["couplingValues"],
        }

        params = np.zeros(len(self.allSymbols), dtype="float64")
        for key, value in paramsDict.items():
            params[self.allSymbols.index(key)] = value

        return params

    def getTConsts(self, T, params):
        ## Should this be moved to DRalgo? Probably
        RGScale = 4.0 * pi * exp(-np.euler_gamma) * T
        Lb = 2.0 * log(RGScale / T) - self.EulerGammaPrime

        params[self.allSymbols.index("RGScale")] = RGScale
        params[self.allSymbols.index("T")] = T
        params[self.allSymbols.index("Lb")] = Lb
        params[self.allSymbols.index("Lf")] = Lb + self.Lfconst

        return params

    def runParams4D(self, paramsDict, T):
        params = self.getTConsts(T, np.zeros(len(self.allSymbols), dtype="float64"))

        muEvaulate = params[self.allSymbols.index("RGScale")]
        for key, spline in paramsDict.items():
            params[self.allSymbols.index(key)] = spline(muEvaulate)

        return params
    


from unittest import TestCase
class TransitionFinderUnitTests(TestCase):
    def test_bIsPerturbativeTrue(self):
        reference = True
        source = [0.7, -0.8, 0]
        pertSymbols = {"lam11", "lam12", "lam12p"}
        allSymbols = ["lam11", "lam12", "lam12p"]

        self.assertEqual(reference, bIsPerturbative(source, pertSymbols, allSymbols))

    def test_bIsPerturbativeFalse(self):
        reference = False
        source = [-12.57, 0, 0]
        pertSymbols = {"lam11", "lam12", "lam12p"}
        allSymbols = ["lam11", "lam12", "lam12p"]

        self.assertEqual(reference, bIsPerturbative(source, pertSymbols, allSymbols))
