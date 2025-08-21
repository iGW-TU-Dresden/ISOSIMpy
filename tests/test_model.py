import numpy as np
import pytest

from ISOSIMpy.model import EPMUnit, Model, PMUnit, Solver


def make_simple_model(target_series=True):
    x = np.ones(100)
    y = None
    if target_series:
        y = np.ones(100)
    m = Model(dt=1.0, lambda_=0.01, input_series=x, target_series=y)
    m.add_unit(EPMUnit(mtt=5.0, eta=1.2), fraction=0.6, prefix="epm", bounds=[(1, 50), (1, 3)])
    m.add_unit(PMUnit(mtt=10.0), fraction=0.4, prefix="pm", bounds=[(1, 50)])
    return m


def test_registry_roundtrip():
    m = make_simple_model()
    v = m.get_vector()
    m.set_vector(v)
    v2 = m.get_vector()
    assert np.allclose(v, v2)


def test_simulate_shapes():
    m = make_simple_model(target_series=False)
    sim = m.simulate()
    assert sim.shape == (100,)


def test_solver_fits_synthetic():
    # generate synthetic data with known params
    true = Model(dt=1.0, lambda_=0.01, input_series=np.ones(100))
    true.add_unit(EPMUnit(mtt=8.0, eta=1.5), fraction=0.5, prefix="epm")
    true.add_unit(PMUnit(mtt=15.0), fraction=0.5, prefix="pm")
    obs = true.simulate()

    m = Model(dt=1.0, lambda_=0.01, input_series=np.ones(100), target_series=obs)
    m.add_unit(EPMUnit(mtt=5.0, eta=2.0), fraction=0.5, prefix="epm", bounds=[(1, 20), (1, 5)])
    m.add_unit(PMUnit(mtt=10.0), fraction=0.5, prefix="pm", bounds=[(1, 30)])

    m.set_vector(m.get_vector("initial", free_only=False), which="value", free_only=False)
    sim_init = m.simulate()
    err_init = float(np.mean((obs - sim_init) ** 2))

    solver = Solver(m)
    sol, sim = solver.solve(maxiter=50, popsize=10)
    # at least should reduce error vs initials
    err_final = float(np.mean((obs - sim) ** 2))
    assert err_final < err_init


def test_solver_respects_fixed():
    m = make_simple_model()
    m.set_fixed("epm.mtt", True)
    fixed_before = m.params["epm.mtt"]["value"]

    solver = Solver(m)
    sol, _ = solver.solve(maxiter=5, popsize=5)
    assert sol["epm.mtt"] == pytest.approx(fixed_before)
