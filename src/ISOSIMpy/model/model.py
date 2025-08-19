import numpy as np
import scipy
from scipy.optimize import differential_evolution


### define functions / model
class Model:
    """
    The model class.

    Attributes
    ----------
    dt : float
        The time step size. Note that the units corresponding to the
        time step size must be consistent with all other time-dependent
        parameters / units. Has dimension [T]
    lambda_ : float
        The decay constant with. Has dimension [1/T]
    input_series : array_like
        The input series. Can have arbitrary units, but must be
        consistent with the target series units.
    target_series : array_like
        The target series. Can have arbitrary units, but must be
        consistent with the input series units.
    steady_state_input : array_like, optional
        The steady-state input. Can have arbitrary units, but must be
        consistent with the input and target series units. Defauls to
        None.
    n_warmup_half_lives : int, optional
        The number of half-lives to use for warmup. Defaults to 2.
    units : list
        The list of model units (each item being an instance of a unit
        class).
    parameters : array_like
        The current parameters of the model. With n_units units, the last
        n_units parameters are the fractions of each unit. In the case of a
        single unit, the last parameter is 1.
    unit_fractions : array_like
        The fractions of each unit in the model; see `parameters`.
    fixed_parameters : array_like
        The parameters that are fixed during calibration. Is a list of
        bools (one for each parameter), where True indicates a fixed
        parameter.
    bounds : array_like
        The bounds for the parameters. Consists of a tuple with the
        structure (lower_bound, upper_bound) for each parameter, even if
        the parameter is fixed.
    initial_parameters : array_like
        The initial parameters of the model; see `parameters`.
    model_is_warm : bool
        Whether the model has been warmed up or not.
    n_warmup : int
        The number of warmup time steps derived from `n_warmup_half_lives`.
    """

    def __init__(
        self,
        dt,
        lambda_,
        input_series,
        target_series,
        steady_state_input=None,
        n_warmup_half_lives=2,
    ):
        """
        The model class initialization.

        Parameters
        ----------
        dt : float
            The time step size. Note that the units corresponding to the
            time step size must be consistent with all other time-dependent
            parameters / units. Has dimension [T]
        lambda_ : float
            The decay constant with. Has dimension [1/T]
        input_series : array_like
            The input series. Can have arbitrary units, but must be
            consistent with the target series units.
        target_series : array_like
            The target series. Can have arbitrary units, but must be
            consistent with the input series units.
        steady_state_input : array_like, optional
            The steady-state input. Can have arbitrary units, but must be
            consistent with the input and target series units. Defauls to
            None.
        n_warmup_half_lives : int, optional
            The number of half-lives to use for warmup. Defaults to 2.

        Returns
        -------
        None
        """
        self.dt = dt
        self.lambda_ = lambda_
        self.input_series = input_series
        self.target_series = target_series
        self.steady_state_input = steady_state_input
        self.n_warmup_half_lives = n_warmup_half_lives

        # list of units
        self.units = []
        # parameters of n individual units
        # last n parameters are fractions of individual units
        self.parameters = []
        # list of unit fractions
        self.unit_fractions = []
        # fixed parameters
        # list of bools; True if fixed, False if free
        # does not include the unit fractions
        self.fixed_parameters = None
        # bounds, does not include the unit fractions
        self.bounds = []
        # initial parameters
        self.initial_parameters = None
        # warmup trigger
        self.model_is_warm = False
        # warmup steps
        self.n_warmup = 0

    def add_unit(self, unit, fraction):
        """
        Add a unit to the model.

        Parameters
        ----------
        unit : Unit
            The unit to add to the model.
        fraction : float
            The fraction of the unit in the model.

        Returns
        -------
        None
        """
        self.units.append(unit)
        self.parameters.extend(unit.parameters)
        self.bounds.extend(unit.bounds)
        self.unit_fractions.append(fraction)

    def warmup(self):
        """
        Warm up the model.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # add warmup period before input series (and target series)
        # define length of warmup period
        # get half life
        t12 = 0.693 / self.lambda_
        # set warmup to approx. 5 half lives
        self.n_warmup = int(t12) * 10
        # create warmup series
        warmup_series = np.ones(self.n_warmup) * self.steady_state_input
        # add warmup series to input series
        self.input_series = np.concatenate((warmup_series, self.input_series))

        if self.target_series is not None:
            # add nans to target series
            warmup_series[:] = np.nan
            self.target_series = np.concatenate((warmup_series, self.target_series))
        return

    def check_model(self):
        """
        Check if the model is valid (check warmup, check parameters, check
        unit fractions).

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # check warmup
        if not self.model_is_warm and self.steady_state_input is not None:
            self.warmup()
            self.model_is_warm = True
        elif not self.model_is_warm and self.steady_state_input is None:
            self.model_is_warm = True
        elif self.model_is_warm:
            pass
        else:
            raise ValueError("Problem with model warmup.")

        # ckeck parameters
        if len(self.parameters) != len(self.fixed_parameters):
            raise ValueError(
                "Number of parameters does not match number"
                " of entries in fixed_parameters. {} != {}".format(
                    len(self.parameters), len(self.fixed_parameters)
                )
            )

        if len(self.parameters) != len(self.bounds):
            raise ValueError(
                "Number of parameters does not match number"
                " of entries in bounds. {} != {}. Note that parameters need"
                " bounds even if they are fixed.".format(len(self.parameters), len(self.bounds))
            )

        if (
            np.asarray(self.unit_fractions).sum() < 0.99
            or np.asarray(self.unit_fractions).sum() > 1.01
        ):
            raise ValueError("Sum of unit fractions does not equal 1.")

    def simulate(self, parameters):
        """
        Simulate the model given parameters

        Parameters
        ----------
        parameters : list
            The parameters to simulate the model with. With n_units units,
            the last n_units parameters are the fractions of each unit. In
            the case of 1 unit, the last parameter is 1.

        Returns
        -------
        sim : np.ndarray
            The simulated series.
        """
        self.parameters = np.array(parameters)

        # check model
        self.check_model()

        # create series of time steps
        # this includes the optional warmup
        n = len(self.input_series)
        t = np.arange(0, n * self.dt, self.dt)

        # get total number of units in model
        # n_units = len(self.units)

        # get empty target
        sim = np.zeros(n)

        # iterate over units and simulate
        param_count = 0
        for num, unit in enumerate(self.units):
            # get number of parameters
            n_params = len(unit.parameters)
            # set parameters
            unit.set_params(*parameters[param_count : (param_count + n_params)])
            # get impulse response
            impulse_response = unit.get_impulse_response(t, self.dt, self.lambda_)
            # convolution
            contribution = (
                scipy.signal.fftconvolve(self.input_series, impulse_response)[:n] * self.dt
            )
            # scale contribution by fraction
            contribution *= self.unit_fractions[num]
            # add to simulation
            sim += contribution
            # update parameter count
            param_count += n_params

        # remove warmup period
        sim = sim[self.n_warmup :]

        return sim

    def handle_fixed_parameters(self, parameters):
        """
        Handle fixed parameters. This is done to conform with the
        differential evolution optimizer.

        Parameters
        ----------
        parameters : list
            The parameters to simulate the model with. With n_units units,
            the last n_units parameters are the fractions of each unit. In
            the case of 1 unit, the last parameter is 1.

        Returns
        -------
        parameters_ : np.ndarray
            The parameters with fixed parameters removed.
        """
        # handle fixed parameters
        # here we get a list of parameters which may miss some fixed
        # parameters
        # get initial parameters which include free and fixed parameters
        # free parameters may be wrong but fixed parameters remain at
        # initial values
        if self.fixed_parameters is not None:
            parameters_ = np.array(self.initial_parameters.copy())
            parameters_[~self.fixed_parameters] = parameters
        else:
            raise ValueError("Fixed parameters not set.")
        return parameters_

    def objfunc(self, parameters):
        """
        Objective function (mean squared error) for calibration.

        Parameters
        ----------
        parameters : list
            The parameters to simulate the model with. With n_units units,
            the last n_units parameters are the fractions of each unit. In
            the case of 1 unit, the last parameter is 1.

        Returns
        -------
        obj : float
            The objective function value.
        """
        parameters_ = self.handle_fixed_parameters(parameters)

        sim = self.simulate(parameters_)
        mask = ~np.isnan(self.target_series[self.n_warmup :]) & ~np.isnan(sim)
        residuals = sim[mask] - self.target_series[self.n_warmup :][mask]

        obj = np.mean(residuals**2)
        return obj

    def set_init_parameters(self, init_parameters):
        """
        Set the initial parameters of the model.

        Parameters
        ----------
        init_parameters : list
            The initial parameters of the model. With n_units units,
            the last n_units parameters are the fractions of each unit. In
            the case of 1 unit, the last parameter is 1.

        Returns
        -------
        None
        """
        self.parameters = init_parameters
        self.initial_parameters = init_parameters

    def set_fixed_parameters(self, fixed_parameters):
        """
        Set the fixed parameters of the model.

        Parameters
        ----------
        fixed_parameters : list
            The parameters that are fixed during calibration. Is a list of
            bools (one for each parameter), where True indicates a fixed
            parameter.

        Returns
        -------
        None
        """
        self.fixed_parameters = np.array(fixed_parameters)

    def solve(self):
        """
        Solve (i.e., calibrate) the model.

        Parameters
        ----------
        None

        Returns
        -------
        parameters_opt_ : np.ndarray
            The optimized parameters.
        sim_opt : np.ndarray
            The simulation with optimized parameters (including warmup).
        """
        if self.target_series is None:
            raise ValueError("Target series not set.")

        # handle bounds
        # just as parameters themselves we need to remove bounds from fixed
        # parameters so that they are not calibrated
        if self.fixed_parameters is not None:
            bounds_ = [b for b, cond in zip(self.bounds, self.fixed_parameters) if not cond]
        else:
            bounds_ = self.bounds

        result = differential_evolution(
            self.objfunc,
            bounds=bounds_,
            maxiter=10000,
            popsize=100,
            mutation=(0.5, 1.99),
            recombination=0.5,
            tol=1e-3,
        )
        parameters_opt = result.x
        # distribute / handle parameters, taking fixed parameters into
        # account
        parameters_opt_ = self.handle_fixed_parameters(parameters_opt)
        sim_opt = self.simulate(parameters_opt_)

        return parameters_opt_, sim_opt


class EPM_Unit:
    """
    Exponential piston flow model unit.

    Attributes
    ----------
    mtt : float
        Mean travel time.
    eta : float
        Ratio of total volume to volume of exponential model (>= 1).
        eta = 1 means only exponential model, eta > 1 means exponential
        model with (eta - 1) part piston flow.
    parameters : list
        List of parameters.
    bounds : list
        The bounds for the parameters. Consists of a tuple with the
        structure (lower_bound, upper_bound) for each parameter.
    """

    def __init__(self, mtt, eta, bounds=None):
        """
        The exponential piston flow model unit initialization.

        Parameters
        ----------
        mtt : float
            Mean travel time.
        eta : float
            Ratio of total volume to volume of exponential model (>= 1).
            eta = 1 means only exponential model, eta > 1 means exponential
            model with (eta - 1) part piston flow.
        bounds : list
            The bounds for the parameters. Consists of a tuple with the
            structure (lower_bound, upper_bound) for each parameter.

        Returns
        -------
        None
        """
        # mean travel time
        self.mtt = mtt
        # ratio of total volume to volume of exponential model (>= 1)
        # eta = 1 means only exponential model
        # eta > 1 means exponential model with (eta - 1) part piston flow
        self.eta = eta
        self.parameters = [self.mtt, self.eta]

        if bounds is not None and self.bounds != []:
            self.bounds = list(bounds)
        else:
            self.bounds = [(0.0, 10000.0), (1.0, 5.0)]

    def set_params(self, mtt, eta):
        """
        Set the parameters of the unit.

        Parameters
        ----------
        mtt : float
            Mean travel time.
        eta : float
            Ratio of total volume to volume of exponential model (>= 1).
            eta = 1 means only exponential model, eta > 1 means exponential
            model with (eta - 1) part piston flow.

        Returns
        -------
        None
        """
        self.mtt = mtt
        self.eta = eta

    def get_impulse_response(self, tau, dt, lambda_):
        """
        Impulse response function for the EPM.

        Parameters
        ----------
        tau : np.ndarray
            1D array of time points
        dt : float
            Time step size
        lambda_ : float
            Decay constant.

        Returns
        -------
        h : np.ndarray
            h(t), the impulse response as 1D array
        """

        # calculate response
        h_prelim = (
            (self.eta / self.mtt)
            * np.exp(-self.eta * tau / self.mtt + self.eta - 1)
            * np.exp(-lambda_ * tau)
        )
        h = np.where(tau < self.mtt * (1 - 1 / self.eta), 0.0, h_prelim)

        return h


class PM_Unit:
    """
    Piston flow model unit.

    Attributes
    ----------
    mtt : float
        Mean travel time.
    parameters : list
        List of parameters.
    bounds : list
        The bounds for the parameters. Consists of a tuple with the
        structure (lower_bound, upper_bound) for each parameter.
    """

    def __init__(self, mtt, bounds=None):
        """
        The piston flow model unit initialization.

        Parameters
        ----------
        mtt : float
            Mean travel time.
        bounds : list
            The bounds for the parameters. Consists of a tuple with the
            structure (lower_bound, upper_bound) for each parameter.

        Returns
        -------
        None
        """
        # mean travel time
        self.mtt = mtt
        self.parameters = [self.mtt]

        if bounds is not None and self.bounds != []:
            self.bounds = list(bounds)
        else:
            self.bounds = [(0.0, 10000.0)]

    def set_params(self, mtt):
        """
        Set the parameters of the unit.

        Parameters
        ----------
        mtt : float
            Mean travel time.

        Returns
        -------
        None
        """
        self.mtt = mtt

    def get_impulse_response(self, tau, dt, lambda_):
        """
        Impulse response function for the EPM.

        Parameters
        ----------
        tau : np.ndarray
            1D array of time points
        dt : float
            Time step size
        lambda_ : float
            Decay constant.

        Returns
        -------
        h : np.ndarray
            h(t), the impulse response as 1D array
        """

        # we compute the combined IRF g(tau) = f(tau) * z(tau)
        # where f(tau) = delta(tau - t_m) and z(tau) = exp(-lambda tau).
        # discretely, delta is approximated as 1/dt at the nearest index.

        h = np.zeros_like(tau)
        # find the index closest to t_m
        idx = int(round(self.mtt / dt))
        if 0 <= idx < len(tau):
            h[idx] = np.exp(-lambda_ * self.mtt) / dt
        return h
