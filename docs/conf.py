"""Sphinx configuration for pycamtasia."""

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "pycamtasia"
copyright = "2019-2026, Isaac Douglas"
author = "Isaac Douglas"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
]

# Theme
html_theme = "furo"
html_title = "pycamtasia"

# Autodoc
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_member_order = "bysource"

# Napoleon (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_ivar = True

# Intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# MyST
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_enable_extensions = ["deflist", "colon_fence", "tasklist", "fieldlist"]

# Suppress highlighting warnings for abbreviated JSON examples with { ... }
suppress_warnings = ["misc.highlighting_failure"]
