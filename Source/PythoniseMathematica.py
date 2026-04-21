import json
from pathlib import Path
import unicodedata
import re

from GenerateModules import generateModules

def pythoniseMathematica(args):
    moduleDirectory = Path(__file__).resolve().parent/"../Build"/args.modelDirectory 
    def loadMatrices(filePath):
        with open(moduleDirectory/filePath, 'r') as file:
            matrices = file.read()
    
        return [matrix.strip().split('\n') for matrix in matrices.strip().split('\n---\n')]

    def getLinesJSON(filePath):
        with open(moduleDirectory/filePath, "r") as fp:
            return json.load(fp)

    def getLines(filePath):
        with open(moduleDirectory/filePath, "r") as fp:
            return fp.read().splitlines()

    allSymbols = getLines(args.allSymbolsFilePath) + ["missing"]
    allSymbols = sorted(
        [replaceGreekSymbols(symbol) for symbol in allSymbols], reverse=True, key=len
    )
    massNames = getLines(args.scalarMassNamesFilePath) 
    for item in splitExpressions(getLines(args.vectorMassesSquaredFilePath)):
        massNames.append(item["identifier"])

    expressionDict = {
        "bounded": {
            "expressions": splitExpressionsArray(
                getLines(args.boundedConditionsFilePath), allSymbols
            ),
            "filePath": args.boundedConditionsFilePath,
        },
        "betaFunctions4D": {
            "expressions": splitExpressionsArray(
                getLines(args.betaFunctions4DFilePath), allSymbols
            ),
            "filePath": args.betaFunctions4DFilePath,
        },
        "hardToSoft": {
            "expressions": splitExpressionsArray(
                getLines(args.hardToSoftFilePath), allSymbols
            ),
            "filePath": args.hardToSoftFilePath,
        },

        "hardScale": {
            "expressions": replaceSymbolsWithIndices(replaceGreekSymbols(
                getLines(args.hardScaleFilePath)[0]), allSymbols
            ),
            "filePath": args.hardScaleFilePath,
        },

        "softScaleRGE": {
            "expressions": splitExpressionsArray(
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
        "massNames": massNames,
    }
    
    if args.softToUltraSoftFilePath:
        expressionDict |= {
            "softToUltraSoft": {
                "expressions": splitExpressionsArray(getLines(args.softToUltraSoftFilePath), allSymbols),
                "filePath": args.softToUltraSoftFilePath,
                },
            "ultraSoftScaleRGE": {
                "expressions": splitExpressionsArray(getLines(args.ultraSoftScaleRGEFilePath), allSymbols),
                "filePath": args.ultraSoftScaleRGEFilePath,
                }
                }

    else:
        expressionDict |= {"softToUltraSoft": "none", 
                           "ultraSoftRGE": "none"}
    
    with open(moduleDirectory/args.pythonisedExpressionsFilePath, "w") as fp:
        json.dump(expressionDict, fp, indent=4)
        
    scalarPermutationMatrix = (splitExpressions(loadMatrices(args.scalarPermutationMatrixFilePath)[0]) 
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
        [splitExpressions(matrix) for matrix in loadMatrices(args.scalarMassMatrixFilePath)],
        getLines(args.scalarMassNamesFilePath),
        scalarPermutationMatrix,
        splitExpressions(loadMatrices(args.scalarRotationMatrixFilePath)[0]),
        splitExpressions(getLines(args.vectorMassesSquaredFilePath)),
        splitExpressions(getLines(args.vectorShortHandsFilePath)),
        args.gccFlags,
        [replaceGreekSymbols(name) for name in getLinesJSON(args.lagranianVariablesFilePath)["fieldSymbols"]],
        args.modelDirectory,
    )
    
    return


def splitExpressionsArray(expressions, allSymbols):
    pythonisedExpressions = splitExpressions(expressions)
    for expression in pythonisedExpressions:
        expression["expression"]= replaceSymbolsWithIndices(expression["expression"], 
                                                            allSymbols)
    return pythonisedExpressions


def splitExpressions(expressions):
    return [splitExpression(expression) for expression in expressions]


def splitExpression(line):
    line = replaceGreekSymbols(line)
    identifier, expression = (
        map(str.strip, line.split("->")) if ("->" in line) else ("missing", line)
    )
    
    return {
        "identifier": identifier,
        "expression": expression
    }

def replaceGreekSymbols(string):
    def replaceGreekCharacter(match):
        characterData = unicodedata.name(match.group(0)).split()
        
        if 'SMALL' in characterData:
            return characterData[-1].lower()
        
        elif 'CAPITAL' in characterData:
            return characterData[-1].capitalize()
    
    return  re.sub(r'[\u0391-\u03A9\u03B1-\u03C9]', replaceGreekCharacter, string)

def replaceSymbolsWithIndices(expression, symbols):
    for idx, symbol in enumerate(symbols):
        expression = expression.replace(symbol, f"params[{idx}]")
    return expression

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
