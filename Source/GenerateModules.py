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
    scalarMassMatrixFilePath,
    scalarMassNames,
    scalarPermutationMatrixFilePath,
    scalarRotationMatrixFilePath,
    vectorMasses,
    vectorShorthands,
    gccFlags,
    fieldNames
):
    
    (CythonModulesDir := Path("../Build/CythonModules")).mkdir(
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
        scalarMassMatrixFilePath,
        scalarMassNames,
        scalarPermutationMatrixFilePath,
        scalarRotationMatrixFilePath,
        vectorMasses,
        vectorShorthands,
        loopOrder,
    )
    
    generateEvaluatePotentialModule(
        CythonModulesDir / "evaluatePotential.pyx", 
        loopOrder,
        allSymbols, 
        fieldNames,
        veffModule,
        computeMassesModule,
    )
    
    generateSetupFile(
        CythonModulesDir / "Setup.py",
        loopOrder, 
        gccFlags,
        args.profile
    )
    #exit()
    compileCythonModules(args.verbose, CythonModulesDir)
    
def generateSetupFile(
    fileName, 
    loopOrder, 
    gccFlags,
    profile
):  
    with open(fileName, 'w') as file:
        file.writelines(Environment().from_string(dedent("""\
            #!/usr/bin/env python3
            # -*- coding: utf-8 -*-
            from setuptools import setup, Extension
            from Cython.Build import cythonize
            extensions = [Extension("evaluatePotential", ["evaluatePotential.pyx"], extra_compile_args = {{gccFlags}})]

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
        profile = profile))
    
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
cpdef evaluatePotential(const double [::1] fields, double [::1] parameters):
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
    scalarMassMatrixFile, 
    scalarMassNames,
    scalarPermutationMatrixFile,
    scalarRotationMatrixFile,
    vectorMasses,
    vectorShorthands,
    loopOrder
):
    with open(scalarMassMatrixFile) as file:
        scalarMassMatrices = [convertMatrixToCythonSyntax(line) for line in file.readlines()]
    
    ## One [ per row and an extra [ to wrap all rows
    scalarMassMatrixSizes = [scalarMassMatrix.count("[")-1 for scalarMassMatrix in scalarMassMatrices]

    if "none" in scalarPermutationMatrixFile.lower():
        scalarPermutationMatrix = None
    else:
        with open(scalarPermutationMatrixFile) as file:
            scalarPermutationMatrix = file.readline()

    with open(scalarRotationMatrixFile) as file:
        scalarRotationMatrix = json.loads(file.read())
    
    return Environment().from_string(dedent("""\
## DEV note: netlib.org hosts documention for lapack/blas
from scipy.linalg import block_diag
from scipy.linalg.cython_lapack cimport dsyevd
from numpy import array, empty, intc
from scipy.linalg.blas import dgemm
from libc.math cimport sqrt

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
cdef void computeMasses(double [::1] params):
{%- for symbol in allSymbols %}
    cdef double {{ symbol }} = params[{{ loop.index0 }}]
{%- endfor %}
    cdef char uplo = 'U' 
    cdef char jobz = {{"'V'" if bEigenVectors else "'N'"}} 
    ## TODO use this to catch errors 
    cdef int info
{%- for scalarMassMatrix in scalarMassMatrices %}
    {%- set i = loop.index0 %}
    {%- set n = scalarMassMatrixSizes[loop.index0] %}
    ## TODO put on stack
    cdef double [::1, :] scalarMassMatrix{{ i }} 
    cdef int n{{ i }} = {{ n }}
    cdef int lda{{ i }} =  {{ n }} 
    cdef double eigenvalues{{ i }}[{{ n }}]
    cdef int lwork{{ i }} = {{1 + 6*n +2*n*n if bEigenVectors else 2*n+1}}
    cdef int liwork{{ i }} = {{3+5*n if bEigenVectors else 1}} 
    cdef double work{{ i }}[{{1 + 6*n +2*n*n if bEigenVectors else 2*n+1}}]
    cdef int iwork{{ i }}[{{3+5*n if bEigenVectors else 1}}] 
    
    ## TODO Only generate the upper right part of the matrix and do stuff like sMM[0] = expression
    scalarMassMatrix{{ i }} = array({{ scalarMassMatrix -}}, dtype=float, order="F")

    dsyevd(&jobz, &uplo,
           &n{{ i }},
           &scalarMassMatrix{{ i }}[0, 0], &lda{{ i }},
           &eigenvalues{{ i }}[0],
           &work{{ i }}[0], &lwork{{ i }},
           &iwork{{ i }}[0], &liwork{{ i }},
           &info)
    if not info:
        if info < 0: 
            print(f"Element {info} of scalarMassMatrix ")

{%- endfor %}

    
{%- if bEigenVectors %}
    eigenVectors = block_diag(
{%- for scalarMassMatrix in scalarMassMatrices %}
        scalarMassMatrix{{ loop.index0 }},
{%- endfor %}
    )

{%- if not scalarPermutationMatrix == none %}
    cdef int scalarPermutationMatrix[12][12]
    scalarPermutationMatrix = {{ scalarPermutationMatrix }}
    ## TODO use fortran version
    eigenVectors = dgemm(1,  scalarPermutationMatrix, eigenVectors)
{%- endif %}

{%- for symbol, indices in scalarRotationMatrix.items() %}
    params[{{allSymbols.index( symbol )}}] = eigenVectors[{{ indices[0] }}][{{ indices[1] }}]
{%- endfor %}
{%- endif %}
{% set scalarMassMatrixLength = (scalarMassNames | length) / (scalarMassMatrices | length) | int %}
{%- for symbol in scalarMassNames %}
    params[{{allSymbols.index( symbol )}}] = eigenvalues{{ (loop.index0 / scalarMassMatrixLength) | int }}[{{ (loop.index0 % scalarMassMatrixLength) | int }}]
{%- endfor %}

{%- for expression in vectorMasses %}
    params[{{allSymbols.index(expression.identifier)}}] = {{ expression.expression }}
{%- endfor %}

{%- for expression in vectorShorthands %}
    params[{{allSymbols.index(expression.identifier)}}] = {{ expression.expression }}
{%- endfor %}
    
        """)).render(
            allSymbols=allSymbols, 
            scalarMassMatrices = scalarMassMatrices,
            scalarMassMatrixSizes = scalarMassMatrixSizes,
            scalarMassNames = scalarMassNames,
            scalarPermutationMatrix = scalarPermutationMatrix,
            scalarRotationMatrix = scalarRotationMatrix,
            vectorMasses = vectorMasses,
            vectorShorthands = vectorShorthands,
            bEigenVectors = 0 if loopOrder ==1 else 1,
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
