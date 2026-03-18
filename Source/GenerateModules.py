from textwrap import dedent
from jinja2 import Environment
from pathlib import Path
import sys
import time
import subprocess
from hashlib import md5
import importlib.util
## Cannot import things from this module as gives cicular import
import PythoniseMathematica as PythoniseMathematica

def generateModules(
    veffExpressions,
    verbose,
    loopOrder,
    profile,
    allSymbols, 
    scalarMatricesExpression,
    scalarMassNames,
    scalarPermutationMatrix,
    scalarRotationMatrix,
    vectorMasses,
    vectorShorthands,
    gccFlags,
    fieldNames,
    modelDirectory,
):
    
    veffModule = generateVeffModule(
        veffExpressions, 
        allSymbols
        )
    
    computeMassesModule = generateComputeMassesModule(
        allSymbols,
        scalarMatricesExpression,
        scalarMassNames,
        scalarPermutationMatrix,
        scalarRotationMatrix,
        vectorMasses,
        vectorShorthands,
        loopOrder,
    )
    
    evaluatePotentialModule = generateEvaluatePotentialModule(
        loopOrder,
        allSymbols, 
        fieldNames,
        veffModule,
        computeMassesModule,
    )
    
    setupModule = generateSetupFile(
        loopOrder, 
        gccFlags,
        profile,
    )
    
    def getHash(filePath):
        try:
            with open(filePath, "r") as f:
                return md5(f.read().encode()).hexdigest()
        except FileNotFoundError:
            return None

    cythonModulesDir = Path(__file__).resolve().parent/"../Build"/modelDirectory/"CythonModules" 
    cythonModulesDir.mkdir(exist_ok=True, parents=True)
    cythonModulesDir = str(cythonModulesDir)
    sys.path.insert(0, cythonModulesDir)

    if (md5(evaluatePotentialModule.encode()).hexdigest() == getHash(f"{cythonModulesDir}/EvaluatePotential{loopOrder}.pyx") and
        md5(setupModule.encode()).hexdigest() == getHash(f"{cythonModulesDir}/Setup{loopOrder}.py") and
        importlib.util.find_spec(f"EvaluatePotential{loopOrder}") is not None):
        
        if verbose:
            print("Using previously compiled code")
        return
    
    with open(f"{cythonModulesDir}/EvaluatePotential{loopOrder}.pyx", "w") as fp:
        fp.write(evaluatePotentialModule)

    with open(f"{cythonModulesDir}/Setup{loopOrder}.py", "w") as fp:
        fp.write(setupModule)
    
    compileCythonModules(verbose, cythonModulesDir, loopOrder)
    
def generateSetupFile(
    loopOrder, 
    gccFlags,
    profile,
):
    return Environment().from_string(dedent("""\
            #!/usr/bin/env python3
            # -*- coding: utf-8 -*-
            from setuptools import setup, Extension
            from Cython.Build import cythonize
            extensions = [Extension("EvaluatePotential{{loopOrder}}", ["EvaluatePotential{{loopOrder}}.pyx"], extra_compile_args = {{gccFlags}})]
            
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
        )
    
def generateEvaluatePotentialModule(
    loopOrder, 
    allSymbols, 
    fieldNames, 
    veffSubModules, 
    computeMassesModule
):
    return Environment().from_string(dedent("""\
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

def generateVeffModule(veffExpressions, allSymbols):
    ## NOTE this is the one thing the can return complex
    results = [mutliLineExpression(expression) for expression in veffExpressions]
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
    scalarPermutationMatrix,
    scalarRotationMatrix,
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
     
    PMAssignment = ("none" if scalarPermutationMatrix == "none" 
        else [[j, i, ele] for i, row in enumerate(scalarPermutationMatrix) for j, ele in enumerate(row)]) 
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
{%- if not PMAssignment == none %}
    {% set n = scalarMassMatrixSizes|sum %}
    cdef double scalarPermutationMatrix[{{n}}][{{n}}]
    {%- for i, j, value in PMAssignment %}
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
            PMAssignment = PMAssignment,
            scalarRotationMatrix = scalarRotationMatrix,
            vectorMasses = vectorMasses,
            vectorShorthands = vectorShorthands,
            )

def mutliLineExpression(expression):
    operations = ["+="]
    expressions = []
    
    netBrackets = 0
    start = 0
    
    for i, char in enumerate(expression):
        if char == '(':
            netBrackets += 1
        elif char == ')':
            netBrackets -= 1
        if char == ' ' and netBrackets == 0:
            ##+1 to catch space
            line = expression[start:i+1]
            if line in ["+ ", "- "]:
                operations.append("+=" if line == "+ " else "-=")
            else:
                expressions.append(convertToCythonSyntax(line))
            start = i + 1
    
    # Any remaining characters should just be expressions
    if start < len(expression):
        line = expression[start:]
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

def compileCythonModules(verbose, cythonFP, loopOrder):
    if verbose:
        print("Compiling cython modules")
    
    ti = time.time()
    result = subprocess.run(
        [sys.executable, f"Setup{loopOrder}.py", "build_ext", "--inplace"],
        cwd=cythonFP,
        capture_output=True,
        text=True,
    )
    tf = time.time()

    if result.returncode != 0:
        print("Compilation failed:")
        print(result.stderr)
        raise RuntimeError("Cython build failed")
    if verbose:        
        print("Cython compilation succeeded:")
        print(result.stdout)
        print(f'Compilation took {tf - ti} seconds.')
    
    # TODO: Add a clean up step to remove any compilation artifacts.
