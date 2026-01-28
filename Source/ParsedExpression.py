from math import log, sqrt
import numpy as np


class ParsedExpressionArray:
    def __init__(self, parsedExpression, fileName):
        self.identifier = parsedExpression["identifier"]
        self.expression = parsedExpression["expression"]
        self.symbols = parsedExpression["symbols"]
        self.fileName = fileName

        self.lambdaExpression = compile(self.expression, "<string>", mode="eval")

    def evaluate(self, params):
        return eval(self.lambdaExpression, {"log": log, "sqrt": sqrt, "params": params})


class ParsedExpressionSystemArray:
    def __init__(self, parsedExpressionSystem, allSymbols, fileName):
        self.parsedExpressions = [
            (
                allSymbols.index(parsedExpression["identifier"]),
                ParsedExpressionArray(parsedExpression, fileName),
            )
            for parsedExpression in parsedExpressionSystem
        ]

        self.allSymbols = allSymbols
        self.fileName = fileName

    def evaluate(self, params):
        newParams = np.array(params)
        for expression in self.parsedExpressions:
            newParams[expression[0]] = expression[1].evaluate(params)

        return newParams

    def evaluateUnordered(self, params):
        return [expression[1].evaluate(params) for expression in self.parsedExpressions]


from unittest import TestCase


class ParsedExpressionUnitTests(TestCase):
    def test_ParsedExpression(self):
        from numpy import pi

        source = {
            "expression": f"sqrt(params[0])/(4*{pi}) + log(params[2])",
            "identifier": "Identifier",
            "symbols": ["lam","dummy", "mssq"],
        }

        reference = 5.400944901447568

        self.assertEqual(
            reference,
            ParsedExpressionArray(source, None).evaluate([100,5j, 100]),
        )

