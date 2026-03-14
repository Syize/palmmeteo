"""
position.py - Position parsing and conversion

This module contains functions for parsing and converting position specifications
in various formats (grid points, distance, domain percentages, degrees).
"""

import re
import numpy as np
from typing import Tuple, Union
from .exceptions import DataError

pos_re = re.compile(r'''^\s*
        (
            (?P<gridpoint> -?\d+(\.\d*)?)
        |
            (?P<distance> -?\d+(\.\d*)?)
            \s* m
        |
            (?P<domain> -?\d+(\.\d*)?)
            \s* %
        |
            (?P<degrees> -?\d+(\.\d*)?)
            (\s* °
                (\s* (?P<minutes> \d+(\.\d*)?) \s* '
                    (\s* (?P<seconds> \d+(\.\d*)?) \s* ")?
                )?
            )?
            (?P<quadrant> [NSEW])
        )
        \s*$''', re.X)

def parse_pos(pos: str, ngrid: int, resol: float) -> Tuple[float, bool]:
    """
    Parse position specified as one of the options (see pos_re).
    
    Parameters
    ----------
    pos : str
        Position string to parse
    ngrid : int
        Number of grid points
    resol : float
        Resolution of grid points
    
    Returns
    -------
    Tuple[float, bool]
        A tuple containing:
        - parsed position value
        - boolean indicating if the position is in degrees
    
    Raises
    ------
    ValueError
        If the position string is invalid
    """

    m = pos_re.match(pos)
    if not m:
        raise DataError('Invalid position format')

    v = m.group('gridpoint')
    if v:
        return float(v), False

    v = m.group('distance')
    if v:
        v = float(v) / resol - 0.5
        eps_grid = 1e-3
        if not -0.5-eps_grid <= v <= ngrid+0.5+eps_grid:
            raise DataError('Position out of grid bounds')
        return v, False

    v = m.group('domain')
    if v:
        v = float(v) * .01
        if not 0. <= v <= 1.:
            raise DataError('Domain percentage must be between 0 and 100%')
        return v * ngrid - 0.5, False

    v = m.group('degrees')
    if v:
        deg = float(v)

        v = m.group('minutes')
        if v:
            deg += float(v) / 60.

        v = m.group('seconds')
        if v:
            deg += float(v) / 3600.

        v = m.group('quadrant')
        if v in 'NE':
            pass
        elif v in 'SW':
            deg = -deg
        else:
            raise DataError('Invalid quadrant. Must be N, S, E, or W')

        return deg, True

    raise DataError('Invalid position format')

# Round to nearest gridpoint
nearest_gridpt = lambda v, ngrid: min(ngrid-1, max(0, round(v)))
