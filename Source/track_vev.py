import importlib
from cmath import sqrt
from unittest import TestCase

import numpy as np
import scipy
from parsed_expression import ParsedExpression, ParsedExpressionSystem
from pythonise_dralgo import replaceGreekSymbols
from utility import printIfVerbose


def isPerturbative(params, pertSymbols, allSymbols):
    for pertSymbol in pertSymbols:
        if abs(params[allSymbols.index(pertSymbol)]) > 4 * np.pi:
            return False 
    return True

class TrackVEV:
    def __init__(self, TRange,
             initialGuesses,
             verbose,
             pythonisedExpressions,
             loopOrder,
             correctVEV,
        ):
        
        self.TRange = TRange
        self.initialGuesses = initialGuesses
        self.verbose = verbose
        
        self.allSymbols = pythonisedExpressions["allSymbols"]["allSymbols"]
        
        self.pertSymbols = {replaceGreekSymbols(symbol) 
                            for symbolSet in ("fourPointSymbols", "yukawaSymbols", "gaugeSymbols")
                            for symbol in pythonisedExpressions["lagranianVariables"]["lagranianVariables"][symbolSet]
                            }

        self.massIndices = [self.allSymbols.index(massName) for massName in pythonisedExpressions["massNames"]]
        self.correctVEVIndex = pythonisedExpressions["lagranianVariables"]["lagranianVariables"]["fieldSymbols"].index(correctVEV) if correctVEV else None
        
        self.hardToSoft = ParsedExpressionSystem(
                             pythonisedExpressions["hardToSoft"],
                             self.allSymbols,
                         )
        
        self.hardScale = ParsedExpression(
                             pythonisedExpressions["hardScale"]["expressions"],
                             pythonisedExpressions["hardScale"]["filePath"],
                         )
        
        self.softScaleRGE = ParsedExpressionSystem(
                             pythonisedExpressions["softScaleRGE"],
                             self.allSymbols,
                         )
        if pythonisedExpressions["softToUltraSoft"] == "none":
            self.softToUltraSoft = None
        else:
            self.softToUltraSoft = ParsedExpressionSystem(
                             pythonisedExpressions["softToUltraSoft"],
                             self.allSymbols,
                         )

            self.ultraSoftScaleRGE = ParsedExpressionSystem(
                             pythonisedExpressions["ultraSoftScaleRGE"],
                             self.allSymbols,
                         )

        
        self.betaFunction4DExpression = ParsedExpressionSystem(
                             pythonisedExpressions["betaFunctions4D"],
                             self.allSymbols,
                         )
        
        self.bounded = ParsedExpressionSystem(
                             pythonisedExpressions["bounded"],
                             self.allSymbols,
                         )

        self.evaluatePotential = importlib.import_module(f"EvaluatePotential{loopOrder}").evaluatePotential_Python
        self.findGlobalMinimumCython = importlib.import_module(f"EvaluatePotential{loopOrder}").findGlobalMinimum

    def trackVEV(self, benchmark):
        minimizationResults = {
            "bmNumber": benchmark["bmNumber"],
            "failureReason": False,
            "T": [],
            "vevDepthReal": [],
            "vevDepthImag": [],
            "vevLocation": [],
            "violatedHardScale":[],
        }
        
        params = np.zeros(len(self.allSymbols), dtype="float64")
        for key, value in benchmark["lagranianParameters"].items():
            if key == "RGScale":
                continue
            params[self.allSymbols.index(key)] = value

        ## Does this make sense if user RGScale > 7.3TMax? Idk why someone might do this though
        muRange = np.linspace(
            benchmark["lagranianParameters"]["RGScale"],
            7.3 * self.TRange[-1],
            len(self.TRange) * 10,
        )

        ## Dev note on solve_ivp numerical instability:
        ## Any none-zero value in initalConditions will be updated even if not
        ## included in beta function 
        ## The number of symbols in all symbols also affects the result
        ## These differences are at or below the tol of sol_ivp
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
            minimizationResults["failureReason"] = solvedBetaFunction.message
            return minimizationResults
        
        betaSpline4D = {
            symbol: scipy.interpolate.CubicSpline(muRange, solvedBetaFunction.y[idx])
            for idx, symbol in enumerate(self.allSymbols)
            if np.any(solvedBetaFunction.y[idx] != solvedBetaFunction.y[idx][0])
        }

        counter = 0
        ## Initialise vevLocation to feed into the minimisation algo so it can
        ## use the location oTidx ==0 and f the previous minimum as a guess for the next
        ## Not ideal as the code has to repeat an initial guess on first T
        vevLocation = np.array(self.initialGuesses[0])

        for Tidx, T in enumerate(self.TRange):
            printIfVerbose(f"Start of temp = {T} loop", self.verbose)
            
            params = np.zeros(len(self.allSymbols), dtype="float64")
            params[self.allSymbols.index("T")] = T
            hardMatchingScale = self.hardScale.evaluate(params)
            for key, spline in betaSpline4D.items():
                params[self.allSymbols.index(key)] = spline(hardMatchingScale)
            
            if not np.all(self.bounded.evaluateUnordered(params)):
                minimizationResults["failureReason"] = f"At {T=} one of the bounded condiditions isn't met."             
                return minimizationResults

                
            if not isPerturbative(params, self.pertSymbols, self.allSymbols):
                minimizationResults["failureReason"] = f"At {T=} and RGScale {hardMatchingScale} a coupling is larger than 4pi"            
                return minimizationResults

            params = self.hardToSoft.evaluate(params)
            params = self.softScaleRGE.evaluate(params)
            if self.softToUltraSoft:
                params = self.softToUltraSoft.evaluate(params)
                params = self.ultraSoftScaleRGE.evaluate(params)
            
            ## Round needed because nlopt result sometimes fp out of bounds
            ## See https://github.com/stevengj/nlopt/issues/625
            
            result =  self.findGlobalMinimumCython(
                np.array(self.initialGuesses + [np.round(vevLocation, 8)], dtype=np.float64), 
                params
            )
            
            if isinstance(result, str):
                minimizationResults["failureReason"] = result            
                return minimizationResults

            vevLocation, vevDepth = result
            
            if Tidx == 0 and self.correctVEVIndex:
                wrongVEV = (
                    abs(vevLocation[self.correctVEVIndex]) < 0.1
                    or any(abs(ele) > 0.1 for idx, ele in enumerate(vevLocation) if idx != self.correctVEVIndex)
                )   

                if wrongVEV:
                    minimizationResults["failureReason"] = f"At {T=} the vev is {vevLocation} which doesn't isn't the form set by correct VEV."
                    return minimizationResults
                   
            ## TODO only check last eigenvalue from each matrix as that is the largest 
            violatedHardScale = False
            for idx in self.massIndices:
                mass = sqrt(params[idx])
                if abs(mass.imag) < 1e-6 and mass.real > np.pi*T :
                    violatedHardScale = True
                    break
            
            minimizationResults["T"].append(T)
            minimizationResults["vevDepthReal"].append(vevDepth.real)
            minimizationResults["vevDepthImag"].append(vevDepth.imag)
            minimizationResults["vevLocation"].append(vevLocation)
            minimizationResults["violatedHardScale"].append(violatedHardScale)
            
            ## TODO add a catch for bad behaviour e.g. dipping in and out symmetric 
            if np.all(np.abs(vevLocation) < 0.1):
                printIfVerbose(f"Symmetric phase found at temp {T}", self.verbose)

                if counter == 3:
                    break

                counter += 1

        minimizationResults["vevLocation"] = np.transpose(
            minimizationResults["vevLocation"]
        ).tolist()

        return minimizationResults

class TrackVEVUnitTests(TestCase):
    def test_isPerturbativeTrue(self):
        reference = True
        source = [0.7, -0.8, 0]
        pertSymbols = {"lam11", "lam12", "lam12p"}
        allSymbols = ["lam11", "lam12", "lam12p"]

        self.assertEqual(reference, isPerturbative(source, pertSymbols, allSymbols))

    def test_IsPerturbativeFalse(self):
        reference = False
        source = [-12.57, 0, 0]
        pertSymbols = {"lam11", "lam12", "lam12p"}
        allSymbols = ["lam11", "lam12", "lam12p"]

        self.assertEqual(reference, isPerturbative(source, pertSymbols, allSymbols))

