"""
utils.py - Deprecated module for backwards compatibility

This module is kept for backwards compatibility only. All functionality has
been moved to separate, smaller modules with single responsibilities.
"""

import warnings

warnings.warn(
    "The utils.py module is deprecated and will be removed in a future version. "
    "Please use the new modular structure instead. The functionality has been "
    "split into: constants.py, position.py, chunking.py, fileutils.py, timeutils.py, "
    "netcdfutils.py, workflow.py, and sliceutils.py.",
    FutureWarning,
    stacklevel=2
)

# Import all classes and functions from the new modules to maintain compatibility
from .constants import ax_, rad, td0, utc, midnight, utcdefault, midnight_of, eps_grid, fext_re
from .position import pos_re
from .constants import where_range
from .position import parse_pos, nearest_gridpt
from .chunking import distribute, distribute_chunks
from .fileutils import find_free_fname, assert_dir
from .timeutils import NotWholeTimestep, tstep, DTIndexer
from .netcdfutils import ensure_dimension, getvar
from .workflow import Workflow
from .sliceutils import SliceExtender, SliceBoolExtender

__all__ = [
    'ax_', 'rad', 'td0', 'utc', 'midnight', 'utcdefault', 'midnight_of',
    'eps_grid', 'fext_re', 'pos_re', 'where_range',
    'parse_pos', 'nearest_gridpt',
    'distribute', 'distribute_chunks',
    'find_free_fname', 'assert_dir',
    'NotWholeTimestep', 'tstep', 'DTIndexer',
    'ensure_dimension', 'getvar',
    'Workflow',
    'SliceExtender', 'SliceBoolExtender'
]
