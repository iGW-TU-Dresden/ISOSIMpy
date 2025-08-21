from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import scipy.signal

from .units import Unit

# Each registry record stores numeric state + metadata used by the solver.
ParamRecord = Dict[str, object]


@dataclass
class Model:
    """Forward model container with a parameter registry.

    The model aggregates units, keeps their mixing fractions, and performs the
    convolution-based simulation. It also manages an explicit parameter
    registry that stores **current values**, **initial values**, **optimizer
    bounds**, and **fixed flags** per parameter.

    Parameters
    ----------
    dt : float
        Time step of the simulation (same units as ``mtt`` used by units).
    lambda_ : float
        Decay constant in 1/time units.
    input_series : ndarray
        Forcing time series (length ``N``).
    target_series : ndarray, optional
        Observed output series (length ``N``); used only for calibration loss.
    steady_state_input : float, optional
        If provided, a warmup of constant input is prepended.
    n_warmup_half_lives : int, optional
        Heuristic warmup scaling in half-lives (kept for compatibility).

    Notes
    -----
    - Units are added via :meth:`add_unit`. The method also registers unit
      parameters into the model's registry.
    - Bounds are **optimization bounds** only and can be provided at add time
      or later via :meth:`set_bounds`.

    """

    dt: float
    lambda_: float
    input_series: np.ndarray
    target_series: Optional[np.ndarray] = None
    steady_state_input: Optional[float] = None
    n_warmup_half_lives: int = 2

    units: List[Unit] = field(default_factory=list)
    unit_fractions: List[float] = field(default_factory=list)

    # Parameter registry: key -> record
    params: Dict[str, ParamRecord] = field(default_factory=dict, init=False)

    # Internal warmup state
    _is_warm: bool = field(default=False, init=False, repr=False)
    _n_warmup: int = field(default=0, init=False, repr=False)

    def add_unit(
        self,
        unit: Unit,
        fraction: float,
        prefix: Optional[str] = None,
        bounds: Optional[List[Tuple[float, float]]] = None,
    ) -> None:
        """Add a unit, register its parameters, and set its mixture fraction.

        Parameters
        ----------
        unit : :class:`~ISOSIMpy.model.units.Unit`
            The unit instance to add.
        fraction : float
            Mixture fraction of this unit in the overall response. Fractions
            should sum to ~1 across all units.
        prefix : str, optional
            Namespace prefix for the unit's parameters (e.g., ``"epm"``). If
            omitted, ``"u{index}"`` is used in insertion order.
        bounds : list of (float, float), optional
            Optimizer bounds for the unit's parameters in the same order as
            returned by ``unit.param_values()``. If omitted, bounds are left
            as ``None`` and can be supplied later via :meth:`set_bounds`.

        Raises
        ------
        ValueError
            If ``bounds`` is provided and its length does not match the number
            of unit parameters.
        """
        idx = len(self.units)
        self.units.append(unit)
        self.unit_fractions.append(float(fraction))

        prefix = prefix or f"u{idx}"
        local_params = list(unit.param_values().items())
        if bounds is not None and len(bounds) != len(local_params):
            raise ValueError("Length of bounds list must match number of unit parameters")

        for i, (local_name, val) in enumerate(local_params):
            key = f"{prefix}.{local_name}"
            b = bounds[i] if bounds is not None else None
            self.params[key] = {
                "value": float(val),
                "initial": float(val),
                "bounds": b,
                "fixed": False,
                "unit_index": idx,
                "local_name": local_name,
            }

    def param_keys(self, free_only: bool = False) -> List[str]:
        """Return parameter keys in a stable order.

        Parameters
        ----------
        free_only : bool, optional
            If ``True``, return only parameters with ``fixed == False``.

        Returns
        -------
        list of str
            Fully-qualified parameter keys (e.g., ``"epm.mtt"``).
        """
        items = sorted(
            self.params.items(), key=lambda kv: (kv[1]["unit_index"], kv[1]["local_name"])  # type: ignore
        )
        return [k for k, rec in items if not (free_only and rec.get("fixed"))]

    def get_vector(self, which: str = "value", free_only: bool = False) -> List[float]:
        """Export parameter values as a flat vector in registry order.

        Parameters
        ----------
        which : {"value", "initial"}
            Whether to export current values or initial guesses.
        free_only : bool, optional
            If ``True``, export only free parameters.

        Returns
        -------
        list of float
            Parameter vector following :meth:`param_keys` order.
        """
        assert which in {"value", "initial"}
        keys = self.param_keys(free_only=free_only)
        return [float(self.params[k][which]) for k in keys]

    def set_vector(
        self, vec: Sequence[float], which: str = "value", free_only: bool = False
    ) -> None:
        """Write a vector into the registry (and units) in registry order.

        Parameters
        ----------
        vec : sequence of float
            Values to assign (length must match the number of addressed params).
        which : {"value", "initial"}
            Destination field to write (``"value"`` also writes through to units).
        free_only : bool, optional
            If ``True``, write into free parameters only.
        """
        assert which in {"value", "initial"}
        keys = self.param_keys(free_only=free_only)
        it = iter(map(float, vec))
        for k in keys:
            v = next(it)
            self.params[k][which] = v
            if which == "value":
                # push through to owning unit immediately
                idx = int(self.params[k]["unit_index"])  # type: ignore
                local = str(self.params[k]["local_name"])  # type: ignore
                self.units[idx].set_param_values({local: v})

    def set_param(self, key: str, value: float) -> None:
        """Set a single parameter's **current** value and update the unit.

        This is a convenience wrapper around :meth:`set_vector` for one value.
        """
        self.params[key]["value"] = float(value)
        idx = int(self.params[key]["unit_index"])  # type: ignore
        local = str(self.params[key]["local_name"])  # type: ignore
        self.units[idx].set_param_values({local: float(value)})

    def set_initial(self, key: str, value: float) -> None:
        """Set a single parameter's **initial** value used for optimization seeding."""
        self.params[key]["initial"] = float(value)

    def set_bounds(self, key: str, bounds: Tuple[float, float]) -> None:
        """Set optimizer bounds for a single parameter.

        Parameters
        ----------
        key : str
            Fully-qualified parameter key (e.g., ``"epm.mtt"``).
        bounds : (float, float)
            Lower and upper search bounds for the optimizer.
        """
        lo, hi = bounds
        self.params[key]["bounds"] = (float(lo), float(hi))

    def set_fixed(self, key: str, fixed: bool = True) -> None:
        """Mark a parameter as fixed (not optimized)."""
        self.params[key]["fixed"] = bool(fixed)

    def get_bounds(self, free_only: bool = False) -> List[Tuple[float, float]]:
        """Return bounds for parameters in registry order.

        Raises a ``ValueError`` if any addressed parameter has no bounds set.
        """
        keys = self.param_keys(free_only=free_only)
        out: List[Tuple[float, float]] = []
        for k in keys:
            b = self.params[k]["bounds"]
            if b is None:
                raise ValueError(f"Missing optimizer bounds for parameter: {k}")
            out.append(b)  # type: ignore[arg-type]
        return out

    @property
    def n_warmup(self) -> int:
        """Number of warmup steps prepended to the series."""
        return self._n_warmup

    def _warmup(self) -> None:
        t12 = 0.693 / self.lambda_
        self._n_warmup = int(t12) * self.n_warmup_half_lives
        if self.steady_state_input is None or self._n_warmup <= 0:
            # no warmup requested → ensure we don't slice anything off
            self._n_warmup = 0
            self._is_warm = True
            return
        warm = np.full(self._n_warmup, float(self.steady_state_input))
        self.input_series = np.concatenate((warm, self.input_series))
        if self.target_series is not None:
            warm_nan = np.full(self._n_warmup, np.nan)
            self.target_series = np.concatenate((warm_nan, self.target_series))
        self._is_warm = True

    def _check(self) -> None:
        if not self._is_warm:
            self._warmup()
        s = sum(self.unit_fractions) if self.unit_fractions else 0.0
        if not (0.99 <= s <= 1.01):
            raise ValueError("Sum of unit fractions must be ~1.0.")

    def simulate(self) -> np.ndarray:
        """Run the forward model using current registry values.

        Returns
        -------
        ndarray
            Simulated output aligned with ``target_series`` (warmup removed).
        """
        self._check()
        n = len(self.input_series)
        t = np.arange(0.0, n * self.dt, self.dt)
        sim = np.zeros(n)
        for frac, unit in zip(self.unit_fractions, self.units):
            h = unit.get_impulse_response(t, self.dt, self.lambda_)
            contrib = scipy.signal.fftconvolve(self.input_series, h)[:n] * self.dt
            sim += frac * contrib
        return sim[self._n_warmup :]

    def write_report(
        self,
        filepath: str,
        frequency: str,
        sim: Optional[np.ndarray] = None,
        title: str = "Model Report",
        include_initials: bool = True,
        include_bounds: bool = True,
    ) -> str:
        """
        Create a simple text report of the current model configuration and fit.

        Parameters
        ----------
        filepath : str
            Path of the text file to write.
        frequency : str
            Simulation frequency (e.g., ``"1h"``). This is not checked
            internally and directly written to the report.
        sim : ndarray, optional
            Simulated series corresponding to the *current* parameters. If not
            provided and `target_series` is present, the method will call
            :meth:`simulate` to compute one.
        title : str, optional
            Title shown at the top of the report.
        include_initials : bool, optional
            Whether to include initial values in the parameter table.
        include_bounds : bool, optional
            Whether to include optimizer bounds in the parameter table.

        Returns
        -------
        str
            The full report text that was written to `filepath`.

        Notes
        -----
        - Parameters are grouped by their namespace prefix (e.g., ``"epm"`` in
          keys like ``"epm.mtt"``).
        - If `target_series` is available, the report includes the mean squared
          error (MSE) between the simulation and observations using overlapping,
          non-NaN entries.

        """
        lines: list[str] = []

        # Header
        lines.append(f"{title}")
        lines.append("=" * max(len(title), 20))
        lines.append("")

        # Model settings
        lines.append("Model settings")
        lines.append("--------------")
        lines.append(f"Time step (dt):          {frequency}")
        lines.append(f"Decay constant (lambda): {self.lambda_}")
        lines.append(f"Warmup steps:            {self._n_warmup} (auto)")
        lines.append(f"Units count:             {len(self.units)}")
        lines.append("")

        # MSE if possible
        mse_text = "n/a"
        if self.target_series is not None:
            if sim is None:
                sim = self.simulate()
            y = self.target_series[self._n_warmup :]
            if y is not None and sim is not None and len(y) == len(sim):
                mask = ~np.isnan(y) & ~np.isnan(sim)
                if np.any(mask):
                    mse = float(np.mean((sim[mask] - y[mask]) ** 2))
                    mse_text = f"{mse:.6g}"
        lines.append("Global fit")
        lines.append("----------")
        lines.append(f"MSE: {mse_text}")
        lines.append("")

        # Parameter table grouped by unit prefix
        lines.append("Parameters by unit")
        lines.append("------------------")
        grouped: dict[str, list[str]] = {}
        for key in self.param_keys(free_only=False):
            prefix = key.split(".", 1)[0] if "." in key else "(root)"
            grouped.setdefault(prefix, []).append(key)

        # pretty print per group
        for idx, prefix in enumerate(sorted(grouped.keys())):
            frac = self.unit_fractions[idx] if idx < len(self.unit_fractions) else None
            frac_str = f"fraction={frac:.3f}" if frac is not None else ""
            lines.append(f"[{prefix}] {frac_str}")
            keys = sorted(grouped[prefix], key=lambda k: self.params[k]["local_name"])  # type: ignore
            for k in keys:
                rec = self.params[k]
                val = float(rec["value"])
                fixed = bool(rec.get("fixed", False))
                row = f"  {k:15s} value={val:.6g}"
                if include_initials:
                    row += f", initial={float(rec['initial']):.6g}"
                if include_bounds and rec.get("bounds") is not None:
                    lo, hi = rec["bounds"]  # type: ignore
                    row += f", bounds=({float(lo):.6g}, {float(hi):.6g})"
                row += f", fixed={fixed}"
                lines.append(row)
            lines.append("")

        report_text = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_text)
        return report_text
