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

    def _simulate_given_free(self, free_params: Sequence[float]) -> np.ndarray:
        """Set free params and return simulation."""
        self.model.set_vector(list(free_params), which="value", free_only=True)
        return self.model.simulate()

    def _obj(self, free_params: Sequence[float]) -> float:
        """Mean squared error objective on the masked overlapping support."""
        sim = self._simulate_given_free(free_params)
        if self.model.target_series is None:
            return float("inf")
        y = self.model.target_series[self.model.n_warmup :]
        mask = ~np.isnan(y) & ~np.isnan(sim)
        if not np.any(mask):
            return float("inf")
        resid = sim[mask] - y[mask]
        return float(np.mean(resid**2))

    def differential_evolution(
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
        sim = self._simulate_given_free(result.x)
        solution = {k: float(self.model.params[k]["value"]) for k in self.model.params}
        return solution, sim

    @staticmethod
    def _log_prior_uniform(theta: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
        """Uniform prior inside [lo, hi], -inf outside."""
        if np.any(theta < lo) or np.any(theta > hi):
            return -np.inf
        return 0.0

    @staticmethod
    def _loglik_from_sim(y_full: np.ndarray, sim: np.ndarray, sigma: float | None) -> float:
        """Gaussian likelihood if sigma given; otherwise σ marginalized (Jeffreys prior)."""
        mask = ~np.isnan(y_full) & ~np.isnan(sim)
        n_eff = int(np.sum(mask))
        if n_eff == 0:
            return -np.inf
        resid = sim[mask] - y_full[mask]
        sse = float(np.dot(resid, resid))
        if not np.isfinite(sse) or sse < 0.0:
            return -np.inf
        if sigma is None:
            # log p(y|θ) ∝ -(n/2) log(SSE)
            if sse <= 0.0:
                sse = 1e-300
            return -0.5 * n_eff * np.log(sse)
        sig2 = float(sigma) ** 2
        return -0.5 * (sse / sig2) - 0.5 * n_eff * np.log(2.0 * np.pi * sig2)

    def mcmc_sample(
        self,
        n_samples: int,
        burn_in: int = 1000,
        thin: int = 1,
        rw_scale: float = 0.05,
        sigma: float | None = None,
        log_prior: callable | None = None,
        start: Sequence[float] | None = None,
        random_state: int | np.random.Generator | None = None,
        return_sim: bool = False,
        set_model_state: bool = False,
    ):
        """Random-Walk Metropolis–Hastings over free parameters.

        Returns a dict with keys:
          - 'param_names', 'samples', 'logpost', 'accept_rate',
            'posterior_mean', 'posterior_map', 'map_logpost', ['sims' if requested]
        """
        rng = (
            np.random.default_rng(random_state)
            if not isinstance(random_state, np.random.Generator)
            else random_state
        )

        if self.model.target_series is None:
            raise ValueError("MCMC requires target_series on the model.")

        y_full = self.model.target_series[self.model.n_warmup :]
        bounds = np.asarray(self._reduced_bounds(), dtype=float)
        lo, hi = bounds[:, 0], bounds[:, 1]
        if np.any(~np.isfinite(lo)) or np.any(~np.isfinite(hi)):
            raise ValueError("All free parameters must have finite bounds for MCMC.")

        keys_free = self.model.param_keys(free_only=True)
        d = len(keys_free)

        # Start vector
        if start is None:
            start_vec = np.asarray(
                self.model.get_vector(which="value", free_only=True), dtype=float
            )
            if np.any(~np.isfinite(start_vec)):
                start_vec = np.asarray(
                    self.model.get_vector(which="initial", free_only=True), dtype=float
                )
            start_vec = np.clip(start_vec, lo, hi)
        else:
            start_vec = np.asarray(start, dtype=float)
            if start_vec.shape != (d,):
                raise ValueError(f"`start` must have length {d}.")
            start_vec = np.clip(start_vec, lo, hi)

        # Proposal steps (diagonal)
        step = rw_scale * (hi - lo)
        step = np.where(step <= 0.0, 1e-12, step)

        # Evaluate initial point
        cur = start_vec.copy()
        cur_lp = log_prior(cur) if log_prior is not None else self._log_prior_uniform(cur, lo, hi)
        if not np.isfinite(cur_lp):
            raise ValueError("Initial point has zero prior density; choose a valid `start`.")
        cur_sim = self._simulate_given_free(cur)
        cur_ll = self._loglik_from_sim(y_full, cur_sim, sigma)
        cur_logpost = cur_lp + cur_ll

        if not np.isfinite(cur_logpost):
            # Try to find a finite start by small jitters
            for _ in range(20):
                trial = np.clip(cur + rng.normal(0.0, step), lo, hi)
                sim = self._simulate_given_free(trial)
                ll = self._loglik_from_sim(y_full, sim, sigma)
                lp = (
                    log_prior(trial)
                    if log_prior is not None
                    else self._log_prior_uniform(trial, lo, hi)
                )
                lpt = lp + ll
                if np.isfinite(lpt):
                    cur, cur_sim, cur_logpost = trial, sim, lpt
                    break
            if not np.isfinite(cur_logpost):
                raise RuntimeError("Failed to find a finite starting point for MCMC.")

        # Storage
        n_keep = n_samples
        total_needed = burn_in + n_keep * thin
        samples = np.empty((n_keep, d), dtype=float)
        logposts = np.empty(n_keep, dtype=float)
        sims = [] if return_sim else None

        # MH loop
        accepts = 0
        keep_idx = 0
        for it in range(total_needed):
            prop = cur + rng.normal(0.0, step, size=d)

            if np.any(prop < lo) or np.any(prop > hi):
                accept = False  # fast reject
            else:
                prop_sim = self._simulate_given_free(prop)
                prop_ll = self._loglik_from_sim(y_full, prop_sim, sigma)
                if np.isfinite(prop_ll):
                    prop_lp = (
                        log_prior(prop)
                        if log_prior is not None
                        else self._log_prior_uniform(prop, lo, hi)
                    )
                    prop_logpost = prop_ll + prop_lp
                else:
                    prop_logpost = -np.inf

                log_alpha = prop_logpost - cur_logpost  # symmetric proposal
                if log_alpha >= 0.0 or np.log(rng.uniform()) < log_alpha:
                    cur, cur_sim, cur_logpost = prop, prop_sim, prop_logpost
                    accept = True
                else:
                    accept = False

            accepts += int(accept)

            if it >= burn_in and ((it - burn_in) % thin == 0):
                samples[keep_idx, :] = cur
                logposts[keep_idx] = cur_logpost
                if return_sim:
                    sims.append(cur_sim.copy())
                keep_idx += 1
                if keep_idx == n_keep:
                    break

        accept_rate = accepts / float(total_needed)
        post_mean_free = samples.mean(axis=0)
        map_idx = int(np.argmax(logposts))
        post_map_free = samples[map_idx].copy()

        posterior_mean = {k: float(v) for k, v in zip(keys_free, post_mean_free)}
        posterior_map = {k: float(v) for k, v in zip(keys_free, post_map_free)}

        if set_model_state:
            self.model.set_vector(post_mean_free.tolist(), which="value", free_only=True)

        out = {
            "param_names": list(keys_free),
            "samples": samples,
            "logpost": logposts,
            "accept_rate": float(accept_rate),
            "posterior_mean": posterior_mean,
            "posterior_map": posterior_map,
            "map_logpost": float(logposts[map_idx]),
        }
        if return_sim:
            out["sims"] = np.asarray(sims, dtype=float)
        return out
