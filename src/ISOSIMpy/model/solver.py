from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.optimize import differential_evolution

from .model import Model


@dataclass
class Solver:
    """Optimization wrapper for :class:`~ISOSIMpy.model.model.Model`.

    The solver interacts **only** with the model's parameter registry. It
    constructs a free-parameter vector and corresponding bounds, runs a chosen
    optimizer, and writes the best solution back to the registry (and thus the
    Units via write-through).

    Notes
    -----
    - The objective is currently mean squared error against ``target_series``.
    - Parameters with ``fixed=True`` are excluded from optimization but their
      current values are honored in the simulation.

    """

    model: Model

    # ------------------------- internals ---------------------------------
    def _reduced_bounds(self) -> List[Tuple[float, float]]:
        """Bounds for free parameters in registry order."""
        return self.model.get_bounds(free_only=True)

    def _compose_full_from_free(self, free_params: Sequence[float]) -> List[float]:
        """Inject free params into the full registry state.

        Parameters
        ----------
        free_params : sequence of float
            Optimizer-provided values for free parameters only.

        Returns
        -------
        list of float
            Full current parameter vector (all parameters, incl. fixed).
        """
        self.model.set_vector(list(free_params), which="value", free_only=True)
        return self.model.get_vector(which="value", free_only=False)

    def _obj(self, free_params: Sequence[float]) -> float:
        """Mean squared error objective on the masked overlapping support."""
        self._compose_full_from_free(free_params)
        sim = self.model.simulate()
        if self.model.target_series is None:
            return float("inf")
        y = self.model.target_series[self.model.n_warmup :]
        mask = ~np.isnan(y) & ~np.isnan(sim)
        if not np.any(mask):
            return float("inf")
        resid = sim[mask] - y[mask]
        return float(np.mean(resid**2))

    def solve(
        self,
        maxiter: int = 10000,
        popsize: int = 100,
        mutation: Tuple[float, float] = (0.5, 1.99),
        recombination: float = 0.5,
        tol: float = 1e-3,
    ) -> Tuple[Dict[str, float], np.ndarray]:
        """Run differential evolution and return the best solution.

        Parameters
        ----------
        maxiter : int, optional
            Max iterations in SciPy's DE.
        popsize : int, optional
            Population size multiplier.
        mutation : (float, float), optional
            DE mutation constants.
        recombination : float, optional
            DE recombination constant.
        tol : float, optional
            Convergence tolerance.

        Returns
        -------
        (dict, ndarray)
            Mapping from parameter key to optimized value, and the simulated
            series at that optimum.
        """
        # Validate bounds exist for all free parameters
        bounds = self._reduced_bounds()

        # Build init vector and repair non-finite initials by midpoint of bounds
        init_free = self.model.get_vector(which="initial", free_only=True)
        keys_free = self.model.param_keys(free_only=True)
        repaired = []
        for k, v, (lo, hi) in zip(keys_free, init_free, bounds):
            if not np.isfinite(v):
                mid = 0.5 * (float(lo) + float(hi))
                self.model.set_initial(k, mid)
                repaired.append((k, v, mid))
        if repaired:
            # (optional) print or log repaired initials
            pass

        # Seed current values from initials for a clean, reproducible start
        init_free = self.model.get_vector(which="initial", free_only=True)
        self.model.set_vector(init_free, which="value", free_only=True)

        result = differential_evolution(
            self._obj,
            bounds=bounds,
            maxiter=maxiter,
            popsize=popsize,
            mutation=mutation,
            recombination=recombination,
            tol=tol,
        )

        # Write back and simulate once more at the best params
        self._compose_full_from_free(result.x)
        sim = self.model.simulate()
        solution = {k: float(self.model.params[k]["value"]) for k in self.model.params}
        return solution, sim
