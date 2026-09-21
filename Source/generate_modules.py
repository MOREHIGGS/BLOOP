import importlib.util
import subprocess
import sys
import time
from collections import defaultdict
from hashlib import md5
from math import sqrt
from pathlib import Path
from textwrap import dedent
import nlopt

from jinja2 import Environment
from utility import printIfVerbose


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
    args,
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
        args.absLocalTolerance,
        args.absGlobalTolerance,
        args.relLocalTolerance,
        args.relGlobalTolerance,
        args.bgfLowerBounds,
        args.bgfUpperBounds,
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
        
        printIfVerbose("Using previously compiled code", verbose)
        return
    
    with open(f"{cythonModulesDir}/EvaluatePotential{loopOrder}.pyx", "w") as fp:
        fp.write(evaluatePotentialModule)
    
    with open(f"{cythonModulesDir}/Setup{loopOrder}.py", "w") as fp:
        fp.write(setupModule)
    
    printIfVerbose("Compiling cython modules", verbose)
    
    ti = time.time()
    test = subprocess.run(
        [sys.executable, f"Setup{loopOrder}.py", "build_ext", "--inplace"],
        cwd=cythonModulesDir,
        capture_output=True,
        check=False,
        text=True,
    )

    if test.returncode:
        print(test.stderr)
        exit()

    printIfVerbose(f'Compilation took {time.time() - ti} seconds.', verbose)

def generateSetupFile(
    loopOrder, 
    gccFlags,
    profile,
):
    gccFlags = [f"-{flag}" for flag in gccFlags]

    return Environment().from_string(dedent("""\
        #!/usr/bin/env python3
        # -*- coding: utf-8 -*-
        from setuptools import setup, Extension
        from Cython.Build import cythonize
        extensions = [Extension(
            "EvaluatePotential{{loopOrder}}", 
            ["EvaluatePotential{{loopOrder}}.pyx"], 
            extra_compile_args = {{gccFlags}},
            libraries = ["nlopt"],
        )]
        
        setup(
            name="Veff_cython",
            ext_modules = cythonize(
                    extensions, 
                    compiler_directives={
                        "language_level": "3", 
                        "boundscheck": False,
                        "nonecheck":False,
                        "wraparound": False,
                        "cdivision": True,
                        "profile": {{profile}},
                        }
            ),
        )
    """)).render(**locals())
    
def generateEvaluatePotentialModule(
    loopOrder, 
    allSymbols, 
    fieldNames, 
    veffSubModules, 
    computeMassesModule,
    absLocalTol,
    absGlobalTol,
    relLocalTol,
    relGlobalTol,
    lowerBounds,
    upperBounds,
):
    globalAlgorithm = nlopt.GN_DIRECT_NOSCAL
    localAlgorithm = nlopt.LN_BOBYQA
    numberOfFields = len(fieldNames) 

    return Environment().from_string(dedent("""\
        from libc.complex cimport csqrt, clog
        cimport cython

        from nlopt cimport *
        cdef extern from "nlopt.h":
            void* nlopt_create(int, unsigned)
            void nlopt_destroy(void*)
            int nlopt_set_min_objective(void*, void*, void*)
            int nlopt_optimize(void*, void*, void*)
            int nlopt_set_lower_bounds(void*, void*)
            int nlopt_set_upper_bounds(void*, void*)
            int nlopt_set_xtol_abs1(void*, double)
            int nlopt_set_xtol_rel(void*, double)

        cpdef findGlobalMinimum(
            double [:, ::1] initialGuesses,
            double [::1] parameters,
        ):
            cdef double deepest
            cdef double depth
            cdef int resultCode
            cdef int minIndex = 0
            cdef int i
            cdef list nloptErrors = [
                "NLOPT_FAILURE",
                "NLOPT_INVALID_ARGS",
                "NLOPT_OUT_OF_MEMORY",
                "NLOPT_ROUNDOFF_LIMITED",
                "NLOPT_FORCED_STOP",
            ]

            deepest, resultCode = runNLoptGlobal(initialGuesses[0], parameters)

            for i in range(1, initialGuesses.shape[0]):
                depth, resultCode = runNLoptLocal(initialGuesses[i], parameters)
                
                if resultCode < 0:
                    return nloptErrors[-resultCode - 1]
                
                if depth < deepest:
                    minIndex = i
                    deepest = depth

            return list(initialGuesses[minIndex]), evaluatePotential_C(&initialGuesses[minIndex,0], &parameters[0])

        cpdef runNLoptLocal(
            double [:] fields,
            double [:] parameters,
        ):
            cdef double upperBounds[{{ numberOfFields }}] 
        {% for bound in upperBounds %}
            upperBounds[{{ loop.index0 }}] = {{ bound }}
        {%- endfor %}

            cdef double lowerBounds[{{ numberOfFields }}] 
        {% for bound in lowerBounds %}
            lowerBounds[{{ loop.index0 }}] = {{ bound }}
        {%- endfor %}

            cdef void* opt = nlopt_create({{ localAlgorithm }}, {{ numberOfFields }})
            nlopt_set_min_objective(opt, <void*>&evaluatePotential_NLopt, <void*>&parameters[0])
            nlopt_set_lower_bounds(opt, &lowerBounds[0])
            nlopt_set_upper_bounds(opt, &upperBounds[0])
            nlopt_set_xtol_abs1(opt, {{ absLocalTol }})
            nlopt_set_xtol_rel(opt, {{ relLocalTol}})

            cdef double depth
            cdef int returnCode
            returnCode = nlopt_optimize(opt, <void*>&fields[0], &depth)
            nlopt_destroy(opt)
            return depth, returnCode

        cdef runNLoptGlobal(
            double [:] fields,
            double [:] parameters,
        ):
            cdef double upperBounds[{{ numberOfFields }}] 
        {% for bound in upperBounds %}
            upperBounds[{{ loop.index0 }}] = {{ bound }}
        {%- endfor %}

            cdef double lowerBounds[{{ numberOfFields }}] 
        {% for bound in lowerBounds %}
            lowerBounds[{{ loop.index0 }}] = {{ bound }}
        {%- endfor %}

            cdef void* opt = nlopt_create({{ globalAlgorithm }}, {{ numberOfFields }})
            nlopt_set_min_objective(opt, <void*>&evaluatePotential_NLopt, <void*>&parameters[0])
            nlopt_set_lower_bounds(opt, &lowerBounds[0])
            nlopt_set_upper_bounds(opt, &upperBounds[0])
            nlopt_set_xtol_abs1(opt, {{ absGlobalTol }})
            nlopt_set_xtol_rel(opt, {{ relGlobalTol}})

            cdef double depth
            cdef int returnCode
            returnCode = nlopt_optimize(opt, <void*>&fields[0], &depth)
            nlopt_destroy(opt)
            return runNLoptLocal(fields, parameters)

        cdef double evaluatePotential_NLopt(unsigned int n, double *fields, double *grad, void *parameters) noexcept:
            return evaluatePotential_C(&fields[0], <double*>parameters).real

        cpdef complex evaluatePotential_Python(double[::1] fields, double[::1] parameters):
                return evaluatePotential_C(&fields[0], &parameters[0])

        cdef complex evaluatePotential_C(double *fields, double *parameters):
        {% for name in fieldNames %}
                parameters[{{ allSymbols.index(name) }}] = fields[{{ loop.index0 }}]
        {%- endfor %}
                computeMasses(parameters)
                return veff(parameters)

        {{computeMassesModule}}

        {{ veffSubModules }}
    """)).render(**locals())

def generateVeffModule(veffExpressions, allSymbols):
    ## NOTE this is the one thing the can return complex
    veffExprs, subExprAssignment = commonSubExprElimination(veffExpressions)

    return Environment().from_string(dedent("""\
        cdef double complex veff(double *params):
        {%- for symbol in allSymbols %}
            cdef double {{ symbol }} = params[{{ loop.index0 }}]
        {%- endfor %}
        {%- for expr in subExprAssignment %}
            {{expr}}
        {%- endfor %}
            cdef double complex v = 0.0
        {%- for expr in veffExprs %}
            v+= {{expr}}
        {%- endfor %}
            return  v
    """)).render(**locals())

def commonSubExprElimination(veffExpressions):
    def findSubExpr(string, sub, start):
        indices = []
        while True:
            index = string.find(sub, start)
            if index == -1:
                break
            indices.append(index)
            start = index + 1
        return indices
    ## sqrt and logs are expensive so compute them once and reuse them
    ## in theory the compiler should do this already but given how large NNLO is
    ## I believe the compiler is skipping some optimisations
    ## Currently this has no measurable impact on perfomance. 
    ## Probably because we are memory bound
    functions = ["csqrt","clog"]
    subExprAssignment = []
    
    for function in functions:
        subExprDict = defaultdict(int)
        for expr in veffExpressions:
            subExprIndices = findSubExpr(expr, function, 0)
            for idx in subExprIndices:
                ## Find all ) after the sub expression
                closeIndices = findSubExpr(expr, ")", idx)
                ## Find a sub string where #( = #) so that we have a whole sub expression
                ## This ensures we capture properly something like log(T/sqrt(x) + (x*x*x)) 
                for idxclose in closeIndices:
                    if expr[idx: idxclose+1].count("(") == expr[idx: idxclose+1].count(")"):
                        break
                    
                subExprDict[expr[idx : idxclose+1]] += 1
        
        for idx, (subExpr, exprCount) in enumerate(subExprDict.items()):
            if exprCount > 2:
                subExprAssignment.append(f"cdef double complex {function}{idx} = {subExpr}")
                for idx2, expr in enumerate(veffExpressions):
                    veffExpressions[idx2]= expr.replace(subExpr, f"{function}{idx}")
    
    return veffExpressions, subExprAssignment

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
    ## Proving this works is left as an excerise for the reader :)    
    scalarMassMatrixSizes = [int(-0.5 +sqrt(1+8*len(expressions))/2) for expressions in scalarMatricesExpressions ]
    ## TODO move this to helper
    eigenvalueAssignment = []
    
    for idxSym, symbol in enumerate(scalarMassNames):
        idxShift = 0
        for idxSize, n in enumerate(scalarMassMatrixSizes):
            if idxSym < n + idxShift:
                eigenvalueAssignment.append((symbol, idxSym - idxShift, idxSize))
                break
            idxShift += n

    bEigenVectors = 0 if loopOrder ==1 else 1

    return Environment().from_string(dedent("""\
        ## DEV note: netlib.org hosts documention for lapack/blas
        ## DEV note: REMINDER THAT FORTRAN IS TRANPOSE RELATIVE TO C
        from scipy.linalg.cython_lapack cimport dsyevd
        from scipy.linalg.cython_blas cimport dgemm
        from libc.math cimport sqrt

        cdef void computeMasses(double *params):
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
            {% for expression in scalarPermutationMatrix %}
            scalarPermutationMatrix{{expression.identifier}}= {{expression.expression}}
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
        {%- for thing in scalarRotationMatrix %}
        {%- if thing.expression != '0.' %}
            params[{{allSymbols.index( thing.expression )}}] = permutatedEV{{thing.identifier}}
        {%- endif %}
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
    """)).render(**locals())

