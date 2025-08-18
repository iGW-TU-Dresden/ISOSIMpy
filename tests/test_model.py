import numpy as np

from ISOSIMpy.model import EPM_Unit, Model, PM_Unit


def test_pm_unit_delta_like():
    dt = 1.0
    lam = 0.0
    m = Model(dt, lam, np.ones(20), None)
    m.add_unit(PM_Unit(3.0), 1.0)
    m.set_init_parameters([3.0])
    m.set_fixed_parameters(np.array([True]))
    y = m.simulate([3.0])
    # delta at index 3 -> output equals input shifted by 3
    assert np.isclose(y[0], 0.0)


def test_epm_convolution_stability():
    dt = 1.0
    lam = 0.0
    x = np.ones(100)
    m = Model(dt, lam, x, None)
    m.add_unit(EPM_Unit(10.0, 1.1), 1.0)
    m.set_init_parameters([10.0, 1.1])
    m.set_fixed_parameters(np.array([True, True]))
    y = m.simulate([10.0, 1.1])
    assert len(y) == len(x) - m.n_warmup  # warmup trimmed
