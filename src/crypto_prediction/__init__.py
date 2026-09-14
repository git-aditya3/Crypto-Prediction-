"""
Crypto Prediction - Core Package
A modular, production-ready cryptocurrency forecasting system.
"""

# Single source of truth for the project version.
# (pyproject.toml reads this dynamically via [tool.setuptools.dynamic].)
__version__ = "0.3.0"
__author__ = "Aditya"

from .config import Config, get_config

__all__ = ["Config", "get_config", "__version__"]
