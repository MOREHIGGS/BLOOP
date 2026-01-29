from math import pi, log, exp
import numpy as np
import scipy
import nlopt
from dataclasses import dataclass, InitVar, field


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

    pertSymbols: frozenset = frozenset({1})

    initialGuesses: tuple = (0,)

    ## idk how to type hint these correctly
    nloptInst: str = "nloptInstance"
    
    hardToSoft: callable = 0
    hardScale: callable = 0
    softScaleRGE: callable = 0
    softToUltraSoft: callable = 0
    betaFunction4DExpression: str = "betaFunction4DExpression"
    bounded: str = "bounded"

    verbose: bool = False

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

        params = np.zeros(len(self.allSymbols), dtype="float64")
        for key, value in benchmark["lagranianParameters"].items():
            params[self.allSymbols.index(key)] = value

        ## What to do if user RGScale > 7.3TMax? Idk why someone might do this though

        muRange = np.linspace(
            benchmark["lagranianParameters"]["RGScale"],
            7.3 * self.TRange[-1],
            len(self.TRange) * 10,
        )

        ## (Maybe) Important note:
        ## Any none-zero value in initalConditions will be updated even if not
        ## included in beta function - leads to differences at the level of the tol
        ## of solve_ivp (default 1e-3%)
        def betaFunction(
                mu, 
                initialConditions
            ):
                return self.betaFunction4DExpression.evaluate(initialConditions) / mu
                
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
        from evaluatePotential  import evaluatePotential
        """For physics reasons we only minimise the real part,
        for nlopt reasons we need to give a redunant grad arg"""
        def VeffWrapper(fields, grad):
            return np.real(
                    evaluatePotential(fields, params3D)
                )

        bestResult = self.nloptInst.nloptGlobal(VeffWrapper, minimumCandidates[0])

        for candidate in minimumCandidates:
            result = self.nloptInst.nloptLocal(VeffWrapper, candidate)
            if result[1] < bestResult[1]:
                bestResult = result

        ## Potential computed again in case its complex
        return bestResult[0], evaluatePotential(bestResult[0], params3D)

    def runParams4D(self, paramsDict, T):
        params = np.zeros(len(self.allSymbols), dtype="float64")
        params[self.allSymbols.index("T")] = T
        
        for key, spline in paramsDict.items():
            params[self.allSymbols.index(key)] = spline(self.hardScale.evaluate(params))

        return params
    


from unittest import TestCase
class TrackVEVUnitTests(TestCase):
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
