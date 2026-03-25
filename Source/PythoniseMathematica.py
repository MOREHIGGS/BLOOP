import json
from sympy.parsing.mathematica import parse_mathematica
from numpy import euler_gamma, pi
from pathlib import Path
import unicodedata
import re

from GenerateModules import generateModules

def replaceGreekSymbols(string):
    def replaceGreekCharacter(match):
        characterData = unicodedata.name(match.group(0)).split()
        
        if 'SMALL' in characterData:
            return characterData[-1].lower()
        
        elif 'CAPITAL' in characterData:
            return characterData[-1].capitalize()
    
    return  re.sub(r'[\u0391-\u03A9\u03B1-\u03C9]', replaceGreekCharacter, string)

def replaceSymbolsConst(string):
    return (
        string.replace("Pi", str(pi))
        .replace("EulerGamma", str(euler_gamma))
        .replace("Glaisher", "1.28242712910062")
    )

def replaceSymbolsWithIndices(expression, symbols):
    for idx, symbol in enumerate(symbols):
        expression = expression.replace(symbol, f"params[{idx}]")
    return expression 

def pythoniseExpressionArray(line, allSymbols):
    expressionDict = pythoniseExpression(line)
    expressionDict["expression"] = replaceSymbolsWithIndices(expressionDict["expression"], allSymbols)
    return expressionDict

def pythoniseExpression(line):
    identifier, expression = (
        map(str.strip, line.split("->")) if ("->" in line) else ("missing", line)
    )
    
    return {
        "identifier": replaceGreekSymbols(identifier),
        "expression": str(parse_mathematica(replaceSymbolsConst(replaceGreekSymbols(expression))))
    }


def pythoniseExpressionSystemArray(expressions, allSymbols):
    return [pythoniseExpressionArray(expression, allSymbols) for expression in expressions]

def pythoniseExpressionSystem(expressions):
    return [pythoniseExpression(expression) for expression in expressions]

def pythoniseExpressionClean(line):
    line = replaceGreekSymbols(line)
    identifier, expression = (
        map(str.strip, line.split("->")) if ("->" in line) else ("missing", line)
    )
    
    return {
        "identifier": identifier,
        "expression": expression
    }

def pythoniseExpressionSystemArrayClean(expressions, allSymbols):
    return [pythoniseExpressionArrayClean(expression, allSymbols) for expression in expressions]

def pythoniseExpressionSystemClean(expressions):
    return [pythoniseExpressionClean(expression) for expression in expressions]

def pythoniseExpressionArrayClean(line, allSymbols):
    expressionDict = pythoniseExpressionClean(line)
    expressionDict["expression"] = replaceSymbolsWithIndices(expressionDict["expression"], allSymbols)
    return expressionDict

def pythoniseMathematica(args):
    moduleDirectory = Path(__file__).resolve().parent/"../Build"/args.modelDirectory 
    def loadMassMatrices(filePath):
        with open(moduleDirectory/filePath, 'r') as file:
            matrices = file.read()
    
        return [matrix.strip().split('\n') for matrix in matrices.strip().split('\n---\n')]

   
    def getLinesJSON(filePath):
        with open(moduleDirectory/filePath, "r") as fp:
            return json.load(fp)

    def getLines(filePath):
        with open(moduleDirectory/filePath, "r") as fp:
            data = fp.readlines()
            return data

    allSymbols = getLinesJSON(args.allSymbolsFilePath) + ["missing"]
    allSymbols = sorted(
        [replaceGreekSymbols(symbol) for symbol in allSymbols], reverse=True, key=len
    )
    
    expressionDict = {
        "bounded": {
            "expressions": pythoniseExpressionSystemArray(
                getLines(args.boundedConditionsFilePath), allSymbols
            ),
            "filePath": args.boundedConditionsFilePath,
        },
        "betaFunctions4D": {
            "expressions": pythoniseExpressionSystemArray(
                getLines(args.betaFunctions4DFilePath), allSymbols
            ),
            "filePath": args.betaFunctions4DFilePath,
        },
        "hardToSoft": {
            "expressions": pythoniseExpressionSystemArrayClean(
                getLines(args.hardToSoftFilePath), allSymbols
            ),
            "filePath": args.hardToSoftFilePath,
        },

        "hardScale": {
            "expressions": pythoniseExpressionArray(
                getLines(args.hardScaleFilePath)[0], allSymbols
            ),
            "filePath": args.hardScaleFilePath,
        },

        "softScaleRGE": {
            "expressions": pythoniseExpressionSystemArrayClean(
                getLines(args.softScaleRGEFilePath), allSymbols
            ),
            "filePath": args.softScaleRGEFilePath,
        },
        
        "allSymbols": {
            "allSymbols": allSymbols,
            "fileName": args.allSymbolsFilePath,
        },
        "lagranianVariables": {
            "lagranianVariables": getLinesJSON(args.lagranianVariablesFilePath),
            "fileName": args.lagranianVariablesFilePath 
        },
    }

    if args.softToUltraSoftFilePath:
        expressionDict |= {
            "softToUltraSoft": {
                "expressions": pythoniseExpressionSystemArrayClean(getLines(args.softToUltraSoftFilePath), allSymbols),
                "filePath": args.softToUltraSoftFilePath,
                },
            "ultraSoftScaleRGE": {
                "expressions": pythoniseExpressionSystemArrayClean(getLines(args.ultraSoftScaleRGEFilePath), allSymbols),
                "filePath": args.ultraSoftScaleRGEFilePath,
                }
                }

    else:
        expressionDict |= {"softToUltraSoft": "none", 
                           "ultraSoftRGE": "none"}
        
    scalarPermutationMatrix = (loadMassMatrices(args.scalarPermutationMatrixFilePath) 
        if args.scalarPermutationMatrixFilePath else "none")
    
    veffExpressions = [
        replaceGreekSymbols(line)
        for veff in [args.veffLOFilePath, args.veffNLOFilePath] + (
        [args.veffNNLOFilePath] if args.loopOrder > 1 else [])
        for line in getLines(veff)
        ]
    
    generateModules(
        veffExpressions,
        args.verbose,
        args.loopOrder,
        args.profile,
        allSymbols, 
        [pythoniseExpressionSystem(matrix) for matrix in loadMassMatrices(args.scalarMassMatrixFilePath)],
        getLinesJSON(args.scalarMassNamesFilePath),
        pythoniseExpressionSystemClean(scalarPermutationMatrix[0]),
        pythoniseExpressionSystemClean(loadMassMatrices(args.scalarRotationMatrixFilePath)[0]),
        pythoniseExpressionSystem(getLines(args.vectorMassesSquaredFilePath)),
        pythoniseExpressionSystem(getLines(args.vectorShortHandsFilePath)),
        args.gccFlags,
        [replaceGreekSymbols(name) for name in getLinesJSON(args.lagranianVariablesFilePath)["fieldSymbols"]],
        args.modelDirectory,
    )
    
    with open(moduleDirectory/args.pythonisedExpressionsFilePath, "w") as fp:
        json.dump(expressionDict, fp, indent=4)
    


from unittest import TestCase


class PythoniseMathematicaUnitTests(TestCase):
    def test_replaceGreekSymbols(self):
        reference = ["lamda", "lamda lamda", "mu", "mu mu", "lamda mu", "mu lamda"]
        source = ["λ", "λ λ", "μ", "μ μ", "λ μ", "μ λ"]

        self.assertEqual(
            reference, [replaceGreekSymbols(sourceString) for sourceString in source]
        )

    def test_subStringArray(self):
        reference = "params[1]*params[0]"
        source = "u*mu"
        allSymbols = sorted(["u", "mu"], key=len, reverse =True)
        self.assertEqual(reference, replaceSymbolsWithIndices(source, allSymbols))

    def test_pythoniseExpression(self):
        reference = {
            "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
            "identifier": "Identifier",
        }

        source = "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]"

        self.assertEqual(reference, pythoniseExpression(source))

    def test_paseExpressionSystem(self):
        reference = [
            {
                "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
                "identifier": "Identifier",
            },
            {
                "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
                "identifier": "Identifier",
            },
            {
                "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
                "identifier": "Identifier",
            },
        ]

        source = [
            "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]",
            "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]",
            "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]",
        ]

        self.assertEqual(reference, pythoniseExpressionSystem(source))

