from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

project = "ISOSIMpy"
author = "Max G. Rudolph"

extensions = [
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_design",
]

# notebook execution (safe default for CI)
nb_execution_mode = "off"  # "cache" or "auto" for execution enabled
nb_execution_timeout = 300

# mock heavy deps during doc builds
autodoc_mock_imports = ["PyQt5", "numpy", "scipy", "matplotlib"]

autosummary_generate = True
autodoc_default_options = {"members": True, "undoc-members": False, "show-inheritance": False}

napoleon_google_docstring = False  # True if using Google style
napoleon_numpy_docstring = True  # True if using NumPy style

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "attrs_inline",
    "attrs_block",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**/.ipynb_checkpoints"]

html_theme = "furo"
html_static_path = ["_static"]
html_logo = "_static/logo.png"
html_title = "ISOSIMpy Documentation"
html_short_title = "ISOSIMpy"
html_show_sphinx = True
html_show_copyright = True

# html_theme_options = {
#     "use_edit_page_button": True,
#     "header_links_before_dropdown": 6,
#     "icon_links": [
#         {
#             "name": "GitHub",
#             "url": "https://github.com/iGW-TU-Dresden/ISOSIMpy",
#             "icon": "fab fa-github-square",
#             "type": "fontawesome",
#         }
#     ],
# }

# use None for inventories (Sphinx 8+)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
}

# do not document re-exported names (prevents duplicate objects)
autosummary_imported_members = False

# Disambiguate short type names in NumPy-style docstrings
napoleon_type_aliases = {
    "Unit": "ISOSIMpy.model.units.Unit",
    "Model": "ISOSIMpy.model.model.Model",
    "Solver": "ISOSIMpy.model.solver.Solver",
}
