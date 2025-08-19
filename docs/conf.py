# docs/conf.py
from __future__ import annotations

import os
import sys
from pathlib import Path

# let Sphinx import the package directly from src/ (no pip install needed)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# avoid GUI backend issues in CI
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

project = "ISOSIMpy"
author = "Max G. Rudolph"

extensions = [
    "myst_parser",  # Markdown support
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",  # NumPy/Google-style docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# mock heavy deps while building docs
autodoc_mock_imports = ["PyQt5", "numpy", "scipy", "matplotlib"]

# autosummary: generate API pages at build time
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": False,
}

# Napoleon (docstring) preferences
napoleon_google_docstring = False  # set True if using Google style
napoleon_numpy_docstring = True  # set True if using NumPy style

# MyST (Markdown) options
myst_enable_extensions = ["colon_fence"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", {}),
    "numpy": ("https://numpy.org/doc/stable/", {}),
    "scipy": ("https://docs.scipy.org/doc/scipy/", {}),
}
