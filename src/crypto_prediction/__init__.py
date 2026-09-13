"""
Crypto Prediction - Core Package
A modular, production-ready cryptocurrency price forecasting system.
"""

__version__ = "0.1.0"
__author__ = "Aditya"

from .config import Config, get_config

__all__ = ["Config", "get_config", "__version__"]
