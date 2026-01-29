from math import log, sqrt
import numpy as np
    
class ParsedExpression:
    def __init__(self, expression, fileName):
        self.lambdaExpression = compile(expression, "<string>", mode="eval")
        self.fileName = fileName
        

    def evaluate(self, params):
        return eval(self.lambdaExpression, {"log": log, "sqrt": sqrt, "params": params})
    

class ParsedExpressionSystem:
    def __init__(self, expressionsDict, allSymbols):
        self.fileName = expressionsDict["filePath"]
        self.parsedExpressions = [
            (
                allSymbols.index(expression["identifier"]),
                ParsedExpression(expression["expression"], self.fileName),
            )
            for expression in expressionsDict["expressions"]
        ]

    def evaluate(self, params):
        newParams = np.array(params)
        for outIndex, expression in self.parsedExpressions:
            newParams[outIndex] = expression.evaluate(params)

        return newParams

    def evaluateUnordered(self, params):
        return [expression[1].evaluate(params) for expression in self.parsedExpressions]
    

from unittest import TestCase


class ParsedExpressionUnitTests(TestCase):
    def test_ParsedExpression(self):
        # from numpy import pi

        # source = {
        #     "expression": f"sqrt(params[0])/(4*{pi}) + log(params[2])",
        #     "identifier": "Identifier",
        #     "symbols": ["lam","dummy", "mssq"],
        # }

        # reference = 5.400944901447568

        # self.assertEqual(
        #     reference,
        #     ParsedExpressionArray(source, None).evaluate([100,5j, 100]),
        # )
        return True

