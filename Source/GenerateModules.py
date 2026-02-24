from textwrap import dedent
from jinja2 import Environment
import numpy as np
import json
from pathlib import Path
import os
import sys
import time
import subprocess
## Cannot import things from this module as gives cicular import
import PythoniseMathematica as PythoniseMathematica



def generateModules(
    args, 
    allSymbols, 
    idk,
    scalarMassNames,
    scalarPermutationMatrixFilePath,
    scalarRotationMatrixFilePath,
    vectorMasses,
    vectorShorthands,
    gccFlags,
    fieldNames
):
    
    (CythonModulesDir := Path("../Build/")).mkdir(
        exist_ok=True, 
        parents=True
    )   
    
    if args.verbose:
        print("Generating cython modules")
    
    loopOrder = args.loopOrder 
    
    veffFilePaths   = [args.loFilePath, args.nloFilePath]
    
    if loopOrder >1:
        veffFilePaths.append(args.nnloFilePath)
   
    veffModule = generateVeffModule(
        veffFilePaths, 
        allSymbols
        )
    
    computeMassesModule = generateComputeMassesModule(
        allSymbols,
        idk,
        scalarMassNames,
        scalarPermutationMatrixFilePath,
        scalarRotationMatrixFilePath,
        vectorMasses,
        vectorShorthands,
        loopOrder,
    )
    userString = "Z2_3HDM" 
    evaluatePotentialFP = CythonModulesDir/userString/f"evaluatePotenital{loopOrder}.pyx"
    generateEvaluatePotentialModule(
        CythonModulesDir/userString/f"EvaluatePotenital{loopOrder}.pyx", 
        loopOrder,
        allSymbols, 
        fieldNames,
        veffModule,
        computeMassesModule,
    )
    generateSetupFile(
        CythonModulesDir/userString/f"Setup.py", 
        loopOrder, 
        gccFlags,
        args.profile,
        evaluatePotentialFP,
    )
    
    compileCythonModules(args.verbose, CythonModulesDir/userString)
    
def generateSetupFile(
    fileName, 
    loopOrder, 
    gccFlags,
    profile,
    evaluatePotentialFP,
): 
    with open(fileName, 'w') as file:
        file.writelines(Environment().from_string(dedent("""\
            #!/usr/bin/env python3
            # -*- coding: utf-8 -*-
            from setuptools import setup, Extension
            from Cython.Build import cythonize
            extensions = [Extension("evaluatePotential", ["EvaluatePotenital1.pyx"], extra_compile_args = {{gccFlags}})]

            setup(
                name="Veff_cython",
                ext_modules = cythonize(
                        extensions, 
                        compiler_directives={
                            "language_level": "3", 
                            "boundscheck": False,
                            "nonecheck":False,
                            "wraparound": False,
                            "profile": {{profile}},
                            }
                ),
            )
            """
        )).render(loopOrder = loopOrder, 
        gccFlags = [f"-{flag}" for flag in gccFlags],
        profile = profile,
        evaluatePotentialFP = evaluatePotentialFP,
        ))
    
def generateEvaluatePotentialModule(
    filename, 
    loopOrder, 
    allSymbols, 
    fieldNames, 
    veffSubModules, 
    computeMassesModule
):
    with open(filename, 'w') as file:
        file.write(Environment().from_string(dedent("""\
from libc.complex cimport csqrt, clog
cimport cython
@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef double complex evaluatePotential(const double [::1] fields, double [::1] parameters):
{% for name in fieldNames %}
    parameters[{{ allSymbols.index(name) }}] = fields[{{ loop.index0 }}]
{%- endfor %}

    computeMasses(parameters)
    return veff(parameters)

{{computeMassesModule}}

{{ veffSubModule }}

    
        """)).render(
        loopOrder=loopOrder, 
        allSymbols=allSymbols, 
        fieldNames=fieldNames, 
        veffSubModule = veffSubModules, 
        computeMassesModule = computeMassesModule
        )
        )
def generateVeffModule(veffFilePaths, allSymbols):
    ## NOTE this is the one thing the can return complex
    results = [mutliLineExpression(veffFP) for veffFP in veffFilePaths]
    opTest = [item for result in results for item in result[0]]
    expressionTest = [item for result in results for item in result[1]]
    test = zip(opTest, expressionTest)
    return Environment().from_string(dedent("""\
@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
cdef double complex veff(double [::1] params):
{%- for symbol in allSymbols %}
    cdef double {{ symbol }} = params[{{ loop.index0 }}]
{%- endfor %}
    cdef double complex a = 0.0
{%- for op, term in opsAndExpressions %}
    a {{ op }} {{ term }}
{%- endfor %}
    return a
    """)).render(allSymbols=allSymbols, opsAndExpressions=test)


def generateComputeMassesModule(
    allSymbols, 
    scalarMatricesExpressions,
    scalarMassNames,
    scalarPermutationMatrixFile,
    scalarRotationMatrixFile,
    vectorMasses,
    vectorShorthands,
    loopOrder,
):
    from math import sqrt 
    ## Proving this works is left as an excerise for the reader :)    
    scalarMassMatrixSizes = [int(-0.5 +sqrt(1+8*len(expressions))/2) for expressions in scalarMatricesExpressions ]

    eigenvalueAssignment = []
    for idxSym, symbol in enumerate(scalarMassNames):
        idxShift = 0
        for idxSize, n in enumerate(scalarMassMatrixSizes):
            if idxSym < n + idxShift:
                eigenvalueAssignment.append((symbol, idxSym - idxShift, idxSize))
                break
            idxShift += n 
    
    if "none" in scalarPermutationMatrixFile.lower():
        scalarPermutationMatrix = None
    else:
        with open(scalarPermutationMatrixFile) as file:
            scalarPermutationMatrix = json.load(file)
        PMAssignment = [[j, i, ele] for i, row in enumerate(scalarPermutationMatrix) for j, ele in enumerate(row)] 
    with open(scalarRotationMatrixFile) as file:
        scalarRotationMatrix = json.loads(file.read())
    
    return Environment().from_string(dedent("""\
## DEV note: netlib.org hosts documention for lapack/blas
## DEV note: REMINDER THAT FORTRAN IS TRANPOSE RELATIVE TO C
from scipy.linalg.cython_lapack cimport dsyevd
from scipy.linalg.cython_blas cimport dgemm
from libc.math cimport sqrt

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
cdef void computeMasses(double [::1] params):
{%- for symbol in allSymbols %}
    cdef double {{ symbol }} = params[{{ loop.index0 }}]
{%- endfor %}
    cdef int info
{%- for scalarMatrixExpressions in scalarMatricesExpressions %}
    {%- set i = loop.index0 %}
    {%- set n = scalarMassMatrixSizes[loop.index0] %}
    cdef double scalarMM{{i}}[{{n}}][{{n}}]
    cdef double eigenvalues{{ i }}[{{ n }}]
    cdef int n{{ i }} = {{ n }}
    cdef int lda{{ i }} =  {{ n }} 
    cdef int lwork{{ i }} = {{1 + 6*n +2*n*n if bEigenVectors else 2*n+1}}
    cdef int liwork{{ i }} = {{3+5*n if bEigenVectors else 1}} 
    cdef double work{{ i }}[{{1 + 6*n +2*n*n if bEigenVectors else 2*n+1}}]
    cdef int iwork{{ i }}[{{3+5*n if bEigenVectors else 1}}] 
    ## TODO(?) check for NaN and inf 
    {% for expression in scalarMatrixExpressions %}
    scalarMM{{i}}{{expression.identifier}}= {{expression.expression}}
    {% endfor %}
    dsyevd({{"'V'" if bEigenVectors else "'N'"}}, 
            'L', &n{{ i }},
           &scalarMM{{ i }}[0][0], &lda{{ i }},
           &eigenvalues{{ i }}[0],
           &work{{ i }}[0], &lwork{{ i }},
           &iwork{{ i }}[0], &liwork{{ i }},
           &info)
    
    if info:
        if info < 0: 
            raise ValueError(f"Argument {-info} to dsyevd had an illegal value for scalarMassMatrix{{i}}")
        else:
            raise RuntimeError(f"dsyevd failed to converge for scalarMassMatrix{{i}} (info={info})")
{%- endfor %}
{%- if bEigenVectors %}
    cdef int i = 0
    cdef int j = 0

    {% set n = scalarMassMatrixSizes|sum %}
    cdef double eigenvectors[{{n}}][{{n}}]
    for i in range({{n}}):
        for j in range({{n}}):
            {% set offset = namespace(value=0) %}
            {% for size in scalarMassMatrixSizes %}
            {% if loop.first %}if{% else %}elif{% endif %} 0<=i-{{offset.value}} < {{size}} and 0<=j-{{offset.value}} < {{size}}:
                eigenvectors[i][j] = scalarMM{{loop.index0}}[i-{{offset.value}}][j-{{offset.value}}]
            {% set offset.value = offset.value + size %}
            {% endfor %}
            else:
                eigenvectors[i][j] = 0
{%- if not scalarPermutationMatrix == none %}
    {% set n = scalarMassMatrixSizes|sum %}
    cdef double scalarPermutationMatrix[{{n}}][{{n}}]
    {%- for i, j, value in scalarPermutationMatrix %}
    scalarPermutationMatrix[{{j}}][{{i}}] = {{value}}
    {%- endfor %}
    cdef double permutatedEV[{{n}}][{{n}}]
    cdef int n = {{n}}
    cdef double alpha = 1.0
    cdef double beta = 0.0 
    dgemm('N', 'N', 
          &n, &n, &n, &alpha,  
          &scalarPermutationMatrix[0][0], &n,
          &eigenvectors[0][0], &n,
          &beta, &permutatedEV[0][0], &n)
{%- endif %}
##Tranpose taken symbolically here for zero overhead handling of fortran - c memory maps
{%- for symbol, indices in scalarRotationMatrix.items() %}
    params[{{allSymbols.index( symbol )}}] = permutatedEV[{{ indices[1] }}][{{ indices[0] }}]
{%- endfor %}
{%- endif %}
{%- for symbol, localIdx, blockIdx in eigenvalueAssignment %}
    params[{{allSymbols.index( symbol )}}] = eigenvalues{{ blockIdx }}[{{localIdx }}]
{%- endfor %}

{%- for expression in vectorMasses %}
    params[{{allSymbols.index(expression.identifier)}}] = {{ expression.expression }}
{%- endfor %}

{%- for expression in vectorShorthands %}
    params[{{allSymbols.index(expression.identifier)}}] = {{ expression.expression }}
{%- endfor %}
        """)).render(
            allSymbols=allSymbols, 
            scalarMatricesExpressions=scalarMatricesExpressions,
            eigenvalueAssignment = eigenvalueAssignment,
            scalarMassMatrixSizes = scalarMassMatrixSizes,
            bEigenVectors = 0 if loopOrder ==1 else 1,
            scalarPermutationMatrix = PMAssignment,
            scalarRotationMatrix = scalarRotationMatrix,
            vectorMasses = vectorMasses,
            vectorShorthands = vectorShorthands,
            )

def mutliLineExpression(filePointer):
    ## Takes an expressions and breaks it down into a mutli line expression
    ## (Cython seems to struggle with the one line NNLO veff)
    
    with open(filePointer, 'r') as file:
        veff = file.read()
    
    operations = ["+="]
    expressions = []
    
    netBrackets = 0
    start = 0
    
    for i, char in enumerate(veff):
        if char == '(':
            netBrackets += 1
        elif char == ')':
            netBrackets -= 1
        if char == ' ' and netBrackets == 0:
            ##+1 to catch space
            line = veff[start:i+1]
            if line in ["+ ", "- "]:
                operations.append("+=" if line == "+ " else "-=")
            else:
                expressions.append(convertToCythonSyntax(line))
            start = i + 1
    
    # Any remaining characters should just be expressions
    if start < len(veff):
        line = veff[start:]
        expressions.append(convertToCythonSyntax(line))
    return operations, expressions

def convertMatrixToCythonSyntax(term):
    term = convertToCythonSyntax(term)
    term = term.replace('{', '[')
    return term.replace('}', ']')
    
def convertToCythonSyntax(term):
    term = term.replace('Sqrt', 'csqrt')
    term = term.replace('Log', 'clog')
    term = term.replace('[', '(')
    term = term.replace(']', ')')
    term = term.replace('^', '**')
    term = PythoniseMathematica.replaceSymbolsConst(term)
    return PythoniseMathematica.replaceGreekSymbols(term)

def compileCythonModules(verbose, cythonModuleDir):
    if not os.path.isfile(cythonModuleDir / "Setup.py"):
        raise FileNotFoundError(f"No Setup.py found in {cythonModuleDir}")
    
    if verbose:
        print("Compiling cython modules")
    
    ti = time.time()
    result = subprocess.run(
        [sys.executable, "Setup.py", "build_ext", "--inplace"],
        cwd=cythonModuleDir,
        capture_output=True,
        text=True,
    )
    tf = time.time()

    if result.returncode != 0:
        print("Compilation failed:")
        print(result.stderr)
        raise RuntimeError("Cython build failed")
    else:
        if verbose:        
            print("Cython compilation succeeded:")
            print(result.stdout)
            print(f'Compilation took {tf - ti} seconds.')
        
    # TODO: Add a clean up step to remove any compilation artifacts.
