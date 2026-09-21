from dataclasses import InitVar, dataclass
import nlopt

@dataclass(frozen=True)
class cNlopt:
    nbrVars: int = 0
    varLowerBounds: tuple[float] = (0,)
    varUpperBounds: tuple[float] = (0,)
    absLocalTol: float = 0
    relLocalTol: float = 0
    absGlobalTol: float = 0
    relGlobalTol: float = 0
    config: InitVar[dict] = None

    def __post_init__(self, config: dict):
        if config:
            self.__init__(**config)

    def nloptGlobal(self, func: callable, initialGuess: list[float]):
        opt = nlopt.opt(nlopt.GN_DIRECT_NOSCAL, self.nbrVars)
        opt.set_min_objective(func)
        opt.set_lower_bounds(self.varLowerBounds)
        opt.set_upper_bounds(self.varUpperBounds)
        opt.set_xtol_abs(self.absGlobalTol)
        opt.set_xtol_rel(self.relGlobalTol)
        opt.set_exceptions_enabled(False)
        return self.nloptLocal(func, opt.optimize(initialGuess))

    def nloptLocal(self, func: callable, initialGuess: list[float]):
        opt = nlopt.opt(nlopt.LN_BOBYQA, self.nbrVars)
        opt.set_min_objective(func)
        opt.set_lower_bounds(self.varLowerBounds)
        opt.set_upper_bounds(self.varUpperBounds)
        opt.set_xtol_abs(self.absLocalTol)
        opt.set_xtol_rel(self.relLocalTol)
        opt.set_exceptions_enabled(False)
        return opt.optimize(initialGuess), opt.last_optimum_value(), opt.last_optimize_result()


def printIfVerbose(string, verbose):
    if verbose:
        print(string)


