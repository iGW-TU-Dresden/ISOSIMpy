from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

# Store the current state of the app in a centralized fashion

ArrayLike = np.ndarray


@dataclass
class AppState:
    is_monthly: bool = True
    tracer: str = "Tritium"
    input_series: Optional[Tuple[ArrayLike, ArrayLike]] = None
    target_series: Optional[Tuple[ArrayLike, ArrayLike]] = None
    selected_units: List[str] = field(default_factory=list)  # registry keys: ["EPM","PM",...]
    unit_fractions: Dict[str, float] = field(default_factory=dict)  # by prefix: {"epm":0.5,...}
    params: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)
    # params[prefix][key] = {"val":..., "lb":..., "ub":..., "fixed":0/1}
    steady_state_input: float = 0.0
    n_warmup_half_lives: int = 2
    last_simulation: Optional[ArrayLike] = None
    last_times: Optional[ArrayLike] = None
