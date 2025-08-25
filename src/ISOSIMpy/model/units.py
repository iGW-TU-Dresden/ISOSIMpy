from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

import numpy as np


class Unit(ABC):
    """Abstract base class for a model unit.

    Concrete units represent hydrological transport schemata and must expose
    and accept their **local** parameter values via a mapping. Units are
    intentionally unaware of optimization bounds; those live in the Model's
    parameter registry.

    Notes
    -----
    - Implementations must keep local parameter names *stable* over time so that
      the Model's registry stays consistent.
    - Names should be short (e.g., ``"mtt"``, ``"eta"``).
    """

    @abstractmethod
    def param_values(self) -> Dict[str, float]:
        """Return current local parameter values.

        Returns
        -------
        Dict[str, float]
            Mapping from local parameter name to value.
        """
        raise NotImplementedError

    @abstractmethod
    def set_param_values(self, values: Dict[str, float]) -> None:
        """Set one or more local parameter values.

        Parameters
        ----------
        values : Dict[str, float]
            Mapping from local parameter name to new value. Keys not present
            are ignored.
        """
        raise NotImplementedError

    @abstractmethod
    def get_impulse_response(self, tau: np.ndarray, dt: float, lambda_: float) -> np.ndarray:
        """Evaluate the unit's impulse response on a time grid.

        Parameters
        ----------
        tau : ndarray
            Non-negative time axis (same spacing as simulation time grid).
        dt : float
            Time step size of the discretization.
        lambda_ : float
            Decay constant (1 / time units of ``tau``).

        Returns
        -------
        ndarray
            Impulse response sampled at ``tau``.
        """
        raise NotImplementedError


@dataclass
class EPMUnit(Unit):
    """Exponential Piston-Flow Model (EPM) unit.

    Parameters
    ----------
    mtt : float
        Mean travel time.
    eta : float
        Ratio of total volume to the exponential reservoir (>= 1). ``eta=1``
        reduces to a pure exponential model; ``eta>1`` adds a piston component.
    """

    mtt: float
    eta: float

    def param_values(self) -> Dict[str, float]:
        """Get parameter values.

        Returns
        -------
        Dict[str, float]
            Mapping from local parameter name to value.
        """
        return {"mtt": float(self.mtt), "eta": float(self.eta)}

    def set_param_values(self, values: Dict[str, float]) -> None:
        """Set one or more local parameter values.

        Parameters
        ----------
        values : Dict[str, float]
            Mapping from local parameter name to new value. Keys not present
            are ignored.
        """
        if "mtt" in values:
            self.mtt = float(values["mtt"])
        if "eta" in values:
            self.eta = float(values["eta"])

    def get_impulse_response(self, tau: np.ndarray, dt: float, lambda_: float) -> np.ndarray:
        """EPM impulse response with decay.

        The continuous-time EPM response (without decay) is
        ``h(τ) = (η/mtt) * exp(-η τ / mtt + η - 1)`` for
        ``τ >= mtt*(1 - 1/η)`` and ``0`` otherwise. We also apply
        an exponential decay term ``exp(-λ τ)``.

        Parameters
        ----------
        tau : ndarray
            Non-negative time axis (same spacing as simulation time grid).
        dt : float
            Time step size of the discretization.
        lambda_ : float
            Decay constant (1 / time units of ``tau``).

        Returns
        -------
        ndarray
            Impulse response evaluated at ``tau``.
        """
        # check for edge cases
        if self.eta <= 1.0 or self.mtt <= 0.0:
            return np.zeros_like(tau)

        # base EPM shape
        h_prelim = (self.eta / self.mtt) * np.exp(-self.eta * tau / self.mtt + self.eta - 1.0)
        cutoff = self.mtt * (1.0 - 1.0 / self.eta)
        h = np.where(tau < cutoff, 0.0, h_prelim)
        # radioactive/first-order decay applied to transit time
        h *= np.exp(-lambda_ * tau)
        return h


@dataclass
class EMUnit(Unit):
    """Exponential Model (EM) unit.

    Parameters
    ----------
    mtt : float
        Mean travel time.
    """

    mtt: float

    def param_values(self) -> Dict[str, float]:
        """Get parameter values.

        Returns
        -------
        Dict[str, float]
            Mapping from local parameter name to value.
        """
        return {"mtt": float(self.mtt)}

    def set_param_values(self, values: Dict[str, float]) -> None:
        """Set one or more local parameter values.

        Parameters
        ----------
        values : Dict[str, float]
            Mapping from local parameter name to new value. Keys not present
            are ignored.
        """
        if "mtt" in values:
            self.mtt = float(values["mtt"])

    def get_impulse_response(self, tau: np.ndarray, dt: float, lambda_: float) -> np.ndarray:
        """EM impulse response with decay.

        The continuous-time EPM response (without decay) is
        ``h(τ) = (1/mtt) * exp(-τ / mtt)``. We also apply an exponential
        decay term ``exp(-λ τ)``.

        Parameters
        ----------
        tau : ndarray
            Non-negative time axis (same spacing as simulation time grid).
        dt : float
            Time step size of the discretization.
        lambda_ : float
            Decay constant (1 / time units of ``tau``).

        Returns
        -------
        ndarray
            Impulse response evaluated at ``tau``.
        """
        # check for edge cases
        if self.mtt <= 0.0:
            return np.zeros_like(tau)

        # base EM shape
        h = (1 / self.mtt) * np.exp(-tau / self.mtt)
        # radioactive/first-order decay applied to transit time
        h *= np.exp(-lambda_ * tau)
        return h


@dataclass
class PMUnit(Unit):
    """Piston-Flow Model (discrete delta at the mean travel time) with decay.

    Parameters
    ----------
    mtt : float
        Mean travel time where all mass is transported as a plug flow.
    """

    mtt: float

    def param_values(self) -> Dict[str, float]:
        """Get parameter values.

        Returns
        -------
        Dict[str, float]
            Mapping from local parameter name to value.
        """
        return {"mtt": float(self.mtt)}

    def set_param_values(self, values: Dict[str, float]) -> None:
        """Set local parameter value.

        Parameters
        ----------
        values : Dict[str, float]
            Mapping from local parameter name to new value. Keys not present
            are ignored.
        """
        if "mtt" in values:
            self.mtt = float(values["mtt"])

    def get_impulse_response(self, tau: np.ndarray, dt: float, lambda_: float) -> np.ndarray:
        """Discrete delta response on the grid with exponential decay.

        The delta is represented by setting the bin at ``round(mtt/dt)`` to
        ``1/dt`` to preserve unit mass in the discrete sum.

        Parameters
        ----------
        tau : ndarray
            Non-negative time axis (same spacing as simulation time grid).
        dt : float
            Time step size of the discretization.
        lambda_ : float
            Decay constant (1 / time units of ``tau``).

        Returns
        -------
        ndarray
            Impulse response evaluated at ``tau``.
        """
        # check for edge cases
        if self.mtt <= 0.0:
            return np.zeros_like(tau)

        h = np.zeros_like(tau)
        idx = int(round(self.mtt / dt))
        if 0 <= idx < len(tau):
            h[idx] = 1.0 / dt
            h[idx] *= np.exp(-lambda_ * self.mtt)
        return h
