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
        
        return  self.assertEqual(
                    7.105170185988092,
                    ParsedExpression("sqrt(params[0])/(4) + log(params[2])", None).evaluate([100,5j, 100]),
                )

