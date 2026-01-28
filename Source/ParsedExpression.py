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
    # def test_ParsedExpression(self):
    #     from numpy import pi

    #     source = {
    #         "expression": f"sqrt(lam)/(4*{pi}) + log(mssq)",
    #         "identifier": "Identifier",
    #         "symbols": ["lam", "mssq"],
    #     }

    #     reference = 5.400944901447568

    #     self.assertEqual(
    #         reference,
    #         ParsedExpression(source, None).evaluate({"lam": 100, "mssq": 100}),
    #     )

    # def test_ParsedExpressionSystem(self):
    #     source = [
    #         {
    #             "expression": "sqrt(lam) + log(mssq)",
    #             "identifier": "Identifier",
    #             "symbols": ["lam", "mssq"],
    #         },
    #         {
    #             "expression": "sqrt(2*lam) + log(mssq)",
    #             "identifier": "Identifier",
    #             "symbols": ["lam", "mssq"],
    #         },
    #     ]

    #     reference = [(14.605170185988092 + 0j), (18.747305809719045 + 0j)]

    #     self.assertEqual(
    #         reference,
    #         ParsedExpressionSystem(source, None).evaluate({"lam": 100, "mssq": 100}),
    #     )
    pass
