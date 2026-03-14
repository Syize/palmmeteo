"""
library.py - Deprecated module for backwards compatibility

This module is kept for backwards compatibility only. All functionality has
been moved to separate, smaller modules with single responsibilities.
"""

import warnings

warnings.warn(
    "The library.py module is deprecated and will be removed in a future version. "
    "Please use the new modular structure instead.",
    FutureWarning,
    stacklevel=2
)

# Import all classes and functions from the new modules to maintain compatibility
from .physics.physics import PalmPhysics
from .utils.units import UnitConverter, InputUnitsInfo, LoadedQuantity
from .data.calculator import QuantityCalculator
from .interpolation.regridder import barycentric, TriRegridder, verify_palm_hinterp, parse_linspace, LatLonRegularGrid
from .utils.time import AssimCycle, HorizonSelection, NCDates
from .data.io import InputGatherer

__all__ = [
    'PalmPhysics',
    'UnitConverter',
    'InputUnitsInfo',
    'LoadedQuantity',
    'QuantityCalculator',
    'barycentric',
    'TriRegridder',
    'verify_palm_hinterp',
    'parse_linspace',
    'LatLonRegularGrid',
    'AssimCycle',
    'HorizonSelection',
    'NCDates',
    'InputGatherer'
]
