"""
data module
===========

This module contains data processing functionality for the PALM-meteo software.
"""

from .calculator import QuantityCalculator
from .io import InputGatherer
from .netcdfutils import ensure_dimension, getvar

__all__ = ['QuantityCalculator', 'InputGatherer', 'ensure_dimension', 'getvar']
