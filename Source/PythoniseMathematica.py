import json
from sympy.parsing.mathematica import parse_mathematica
from numpy import euler_gamma, pi
from pathlib import Path
import unicodedata
import re

from GenerateModules import generateModules

def getLines(relativePathToResource):
    with open(relativePathToResource, "r", encoding="utf-8") as fp:
        ## This is a hack to deal with adding hardScale super late to this part of the code
        ## Would be better to do something like  fp.read().strip()
        ## But that breaks existing code and I don't wanna fix that right now, 
        ## especially with our plans of replacing these parsed expressions with meta cython code
        data = fp.readlines()
        if len(data) == 1:
            return data[0]
        return data

def getLinesJSON(relativePathToResource):
    with open(relativePathToResource, "r") as fp:
        return json.load(fp)


def replaceGreekSymbols(string):
    def replaceGreekCharacter(match):
        characterData = unicodedata.name(match.group(0)).split()
        
        if 'SMALL' in characterData:
            return characterData[-1].lower()
        
        elif 'CAPITAL' in characterData:
            return characterData[-1].capitalize()
    
    greekCharacters = r'[\u0391-\u03A9\u03B1-\u03C9]'
    result = re.sub(greekCharacters, replaceGreekCharacter, string)
    
    return result


def replaceSymbolsConst(string):
    return (
        string.replace("Pi", str(pi))
        .replace("EulerGamma", str(euler_gamma))
        .replace("Glaisher", "1.28242712910062")
    )


def removeSuffices(string):
    return string.replace("^2", "sq")


def replaceSymbolsWithIndices(expression, symbols):
    expression = replaceGreekSymbols(expression)
    ## Reverse needed to deal with lam23 and lam23p i.e. substring replaces larger full string
    for idx, symbol in enumerate(sorted(symbols, reverse=True)):
        expression = expression.replace(symbol, f"params[{idx}]")

    return expression


def pythoniseExpressionArray(line, allSymbols):
    identifier, line = (
        map(str.strip, line.split("->")) if ("->" in line) else ("missing", line)
    )
    identifier = removeSuffices(replaceGreekSymbols(identifier))
    expression = parse_mathematica(replaceSymbolsConst(replaceGreekSymbols(line)))
    symbols = [str(symbol) for symbol in expression.free_symbols]

    return {
        "identifier": identifier,
        "expression": replaceSymbolsWithIndices(str(expression), allSymbols),
        "symbols": sorted(symbols),
    }


def pythoniseExpression(line):
    identifier, line = (
        map(str.strip, line.split("->")) if ("->" in line) else ("missing", line)
    )

    identifier = removeSuffices(replaceGreekSymbols(identifier))
    expression = parse_mathematica(replaceSymbolsConst(replaceGreekSymbols(line)))
    symbols = [str(symbol) for symbol in expression.free_symbols]

    return {
        "identifier": identifier,
        "expression": str(expression),
        "symbols": sorted(symbols),
    }


def pythoniseExpressionSystemArray(lines, allSymbols):
    return [pythoniseExpressionArray(line, allSymbols) for line in lines]


def pythoniseExpressionSystem(lines):
    return [pythoniseExpression(line) for line in lines]

def loadMassMatrices(filePath):
    with open(filePath, 'r') as file:
        matrices = file.read()
    
    return [matrix.strip().split('\n') for matrix in matrices.strip().split('\n---\n')]

def pythoniseMathematica(args):
    allSymbols = getLinesJSON(args.allSymbolsFilePath) + ["missing"]
    allSymbols = sorted(
        [replaceGreekSymbols(symbol) for symbol in allSymbols], reverse=True
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
            "expressions": pythoniseExpressionSystemArray(
                getLines(args.hardToSoftFilePath), allSymbols
            ),
            "filePath": args.hardToSoftFilePath,
        },

        "hardScale": {
            "expressions": pythoniseExpressionArray(
                getLines(args.hardScaleFilePath), allSymbols
            ),
            "filePath": args.hardScaleFilePath,
        },

        "softScaleRGE": {
            "expressions": pythoniseExpressionSystemArray(
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
    if args.softToUltraSoftFilePath.lower() == "none":
        expressionDict |= {"softToUltraSoft": "none"}
        
    else:
        expressionDict |= {"softToUltraSoft": {
                    "expressions": pythoniseExpressionSystemArray(
                        getLines(args.softToUltraSoftFilePath), allSymbols
                    ),
                    "filePath": args.softToUltraSoftFilePath,
                }}
        
    generateModules(
        args, 
        allSymbols, 
        [pythoniseExpressionSystem(matrix) for matrix in loadMassMatrices("../Build/Z2_3HDM/DRalgoOutputFiles/test.txt")],
        getLinesJSON(args.scalarMassNamesFilePath),
        args.scalarPermutationMatrixFilePath, 
        args.scalarRotationMatrixFilePath, 
        pythoniseExpressionSystem(getLines(args.vectorMassesSquaredFilePath)),
        pythoniseExpressionSystem(getLines(args.vectorShortHandsFilePath)),
        args.gccFlags,
        [replaceGreekSymbols(name) for name in getLinesJSON(args.lagranianVariablesFilePath)["fieldSymbols"]]
    )
    (outputFile := Path(args.pythonisedExpressionsFilePath)).parent.mkdir(
        exist_ok=True, parents=True
    )   
    with open(outputFile, "w") as fp:
        json.dump(expressionDict, fp, indent=4)
    


from unittest import TestCase


class PythoniseMathematicaUnitTests(TestCase):
    def test_replaceGreekSymbols(self):
        reference = ["lamda", "lamda lamda", "mu", "mu mu", "lamda mu", "mu lamda"]
        source = ["λ", "λ λ", "μ", "μ μ", "λ μ", "μ λ"]

        self.assertEqual(
            reference, [replaceGreekSymbols(sourceString) for sourceString in source]
        )

    def test_removeSuffices(self):
        reference = ["myVarsq", "sqmyVar"]

        source = ["myVar^2", "^2myVar"]

        self.assertEqual(
            reference, [removeSuffices(sourceString) for sourceString in source]
        )

    def test_pythoniseExpression(self):
        reference = {
            "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
            "identifier": "Identifier",
            "symbols": ["lamda", "mssq"],
        }

        source = "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]"

        self.assertEqual(reference, pythoniseExpression(source))

    def test_paseExpressionSystem(self):
        reference = [
            {
                "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
                "identifier": "Identifier",
                "symbols": ["lamda", "mssq"],
            },
            {
                "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
                "identifier": "Identifier",
                "symbols": ["lamda", "mssq"],
            },
            {
                "expression": "0.07957747154594767*sqrt(lamda) + log(mssq)",
                "identifier": "Identifier",
                "symbols": ["lamda", "mssq"],
            },
        ]

        source = [
            "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]",
            "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]",
            "Identifier -> Sqrt[λ] / (4 * Pi) + Log[mssq]",
        ]

        self.assertEqual(reference, pythoniseExpressionSystem(source))

