#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018-2024 Institute of Computer Science of the Czech Academy of
# Sciences, Prague, Czech Republic. Authors: Pavel Krc, Martin Bures, Jaroslav
# Resler.
#
# This file is part of PALM-METEO.
#
# PALM-METEO is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# PALM-METEO is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# PALM-METEO. If not, see <https://www.gnu.org/licenses/>.

"""
A collection of simple, technical utilities.

These utilities need to be stateless, i.e. they must not depend on config or
runtime.
"""

import os
import re
import datetime
from dataclasses import dataclass
import numpy as np
from typing import Any, List, Tuple, Union, Optional, Callable

from .logging import die, warn, log, verbose

# Numeric constants
ax_ = np.newaxis
rad = np.pi / 180.

# Time-related constants
td0 = datetime.timedelta(0)
utc = datetime.timezone.utc
midnight = datetime.time(0)

utcdefault: Callable[[datetime.datetime], datetime.datetime] = lambda dt: dt.replace(tzinfo=utc) if dt.tzinfo is None else dt
midnight_of: Callable[[datetime.datetime], datetime.datetime] = lambda dt: datetime.datetime.combine(dt.date(), midnight, dt.tzinfo)

# Other
eps_grid = 1e-3 #Acceptable rounding error for grid points
fext_re = re.compile(r'\.(\d{3})$')
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

# Returns min and max+1 indices of true values (such that mask[fr:to] is the
# bounding box)
where_range = lambda mask: (np.argmax(mask), len(mask)-np.argmax(mask[::-1]))

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
        raise ValueError()

    v = m.group('gridpoint')
    if v:
        return float(v), False

    v = m.group('distance')
    if v:
        v = float(v) / resol - 0.5
        if not -0.5-eps_grid <= v <= ngrid+0.5+eps_grid:
            raise ValueError()
        return v, False

    v = m.group('domain')
    if v:
        v = float(v) * .01
        if not 0. <= v <= 1.:
            raise ValueError()
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
            raise ValueError()

        return deg, True

    raise ValueError()

# Round to nearest gridpoint
nearest_gridpt = lambda v, ngrid: min(ngrid-1, max(0, round(v)))

def distribute(what: int, into: int, reverse: bool = False) -> Tuple[int, ...]:
    """
    Distributes integer into integers as evenly as possible.
    
    Parameters
    ----------
    what : int
        Number to distribute
    into : int
        Number of parts to distribute into
    reverse : bool, optional
        Whether to reverse the distribution (smaller parts first), by default False
    
    Returns
    -------
    Tuple[int, ...]
        Tuple of integers representing the distribution
    """
    d, m = divmod(what, into)
    if reverse:
        return (d,)*(into-m) + (d+1,)*m
    else:
        return (d+1,)*m + (d,)*(into-m)

def distribute_chunks(sizes: Tuple[int, ...], nthreads: int, 
                     prefix: Tuple[Any, ...] = (), 
                     reverse: bool = False) -> Any:
    """
    Distributes an n-dim array among threads as evenly as possible.
    
    Parameters
    ----------
    sizes : Tuple[int, ...]
        Dimensions of the array to distribute
    nthreads : int
        Number of threads to distribute across
    prefix : Tuple[Any, ...], optional
        Prefix for the distribution, by default ()
    reverse : bool, optional
        Whether to reverse the distribution, by default False
    
    Returns
    -------
    generator
        Generator yielding tuples representing the chunk distribution
    """

    if len(sizes) == 0:
        # Nothing more to distribute, may yield less threads
        yield prefix
    elif sizes[0] >= nthreads:
        # Final step, threads cover remaining dimension(s)
        rem = tuple(slice(0, l) for l in sizes[1:])
        start = 0
        for n in distribute(sizes[0], nthreads, not reverse):
            stop = start + n
            yield prefix + (slice(start, stop),) + rem
            start = stop
    else:
        # distribute threads into this dim's elements
        start = 0
        for n in distribute(nthreads, sizes[0], reverse):
            stop = start + 1
            # By flipping reverse back and forth we avoid systematic
            # overburdening of first/last threads
            yield from distribute_chunks(sizes[1:], n,
                    prefix + (slice(start, stop),),
                    not reverse)
            start = stop

def find_free_fname(fpath: str, overwrite: bool = False) -> str:
    if not os.path.exists(fpath):
        return fpath

    if overwrite:
        log('Existing file {} will be overwritten.', fpath)
        return fpath

    # Try to find free fpath.###
    path, base = os.path.split(fpath)
    nbase = len(base)
    maxnum = -1
    for fn in os.listdir(path):
        if not fn.startswith(base):
            continue
        m = fext_re.match(fn[nbase:])
        if not m:
            continue
        maxnum = max(maxnum, int(m.group(1)))
    if maxnum >= 999:
        raise RuntimeError('Cannot find free filename starting with ' + fpath)

    newpath = '{}.{:03d}'.format(fpath, maxnum+1)
    log('Filename {} exists, using {}.', fpath, newpath)
    return newpath

class NotWholeTimestep(ValueError):
    pass

def tstep(td: datetime.timedelta, step: datetime.timedelta) -> int:
    """
    Fully divide datetime td by timedelta step.
    
    Parameters
    ----------
    td : datetime.timedelta
        Timedelta to divide
    step : datetime.timedelta
        Step size
    
    Returns
    -------
    int
        Number of whole steps
    
    Raises
    ------
    NotWholeTimestep
        If td is not a whole multiple of step
    """
    d, m = divmod(td, step)
    if m:
        raise NotWholeTimestep(f'{td} is not a whole timestep of {step}!')
    return d

def ensure_dimension(f: Any, dimname: str, dimsize: Optional[int]) -> Any:
    """
    Creates a dimension in a netCDF file or verifies its size if it already
    exists.
    
    Parameters
    ----------
    f : netCDF4.Dataset
        NetCDF file object
    dimname : str
        Name of the dimension to create or verify
    dimsize : int or None
        Size of the dimension. If None, creates an unlimited dimension.
    
    Returns
    -------
    netCDF4.Dimension
        Dimension object
    """
    try:
        d = f.dimensions[dimname]
    except KeyError:
        # Dimension is missing - create it and return
        return f.createDimension(dimname, dimsize)

    # Dimension is present
    if dimsize is None:
        # Wanted unlimited dim, check that it is
        if not d.isunlimited():
            raise RuntimeError('Dimension {} is already present and it is '
                    'not unlimited as requested.'.format(dimname))
    else:
        # Fixed size dim - compare sizes
        if len(d) != dimsize:
            raise RuntimeError('Dimension {} is already present and its '
                    'size {} differs from requested {}.'.format(dimname,
                        len(d), dimsize))
    return d

def getvar(f: Any, varname: str, *args: Any, **kwargs: Any) -> Any:
    """
    Creates a variable in a netCDF file or returns it if it already exists.
    Does NOT verify its parameters.
    
    Parameters
    ----------
    f : netCDF4.Dataset
        NetCDF file object
    varname : str
        Name of the variable to create or retrieve
    *args : Any
        Additional positional arguments for createVariable
    **kwargs : Any
        Additional keyword arguments for createVariable
    
    Returns
    -------
    netCDF4.Variable
        Variable object
    """
    try:
        v = f.variables[varname]
    except KeyError:
        return f.createVariable(varname, *args, **kwargs)
    return v

def assert_dir(filepath: str) -> None:
    """
    Creates a directory for an output file if it doesn't exist already.
    
    Parameters
    ----------
    filepath : str
        Path to the file for which to ensure the directory exists
    """
    dn = os.path.dirname(filepath)
    if not os.path.isdir(dn):
        os.makedirs(dn)

@dataclass
class DTIndexer:
    """
    Calculates integral time index from start and origin. Avoids
    using the unpicklable lambdas.
    """
    origin: datetime.datetime
    timestep: datetime.timedelta

    def __call__(self, dt: datetime.datetime) -> int:
        """
        Calculate integral time index from given datetime.
        
        Parameters
        ----------
        dt : datetime.datetime
            Datetime to calculate index for
        
        Returns
        -------
        int
            Integral time index
        
        Raises
        ------
        NotWholeTimestep
            If dt - origin is not a whole timestep
        """
        return tstep(dt-self.origin, self.timestep)

class SliceExtender:
    __slots__ = ['slice_obj', 'slices']

    def __init__(self, slice_obj: Any, *slices: Any):
        """
        Initialize a SliceExtender instance.
        
        Parameters
        ----------
        slice_obj : Any
            Object that supports slicing
        *slices : Any
            Slices to extend
        """
        self.slice_obj = slice_obj
        self.slices = slices

    def __getitem__(self, key: Union[slice, Tuple[slice, ...]]) -> Any:
        """
        Apply extended slicing.
        
        Parameters
        ----------
        key : Union[slice, Tuple[slice, ...]]
            Slice or tuple of slices to apply
        
        Returns
        -------
        Any
            Result of the extended slicing
        """
        if isinstance(key, tuple):
            return self.slice_obj[key+self.slices]
        else:
            return self.slice_obj[(key,)+self.slices]

class SliceBoolExtender:
    __slots__ = ['slice_obj', 'slices', 'boolindex']

    def __init__(self, slice_obj: Any, slices: Tuple[Any, ...], boolindex: Any):
        """
        Initialize a SliceBoolExtender instance.
        
        Parameters
        ----------
        slice_obj : Any
            Object that supports slicing
        slices : Tuple[Any, ...]
            Slices to extend
        boolindex : Any
            Boolean index to apply
        """
        self.slice_obj = slice_obj
        self.slices = slices
        self.boolindex = boolindex

    def __getitem__(self, key: Union[slice, Tuple[slice, ...]]) -> Any:
        """
        Apply extended slicing with boolean index.
        
        Parameters
        ----------
        key : Union[slice, Tuple[slice, ...]]
            Slice or tuple of slices to apply
        
        Returns
        -------
        Any
            Result of the extended slicing with boolean index applied
        """
        if isinstance(key, tuple):
            v = self.slice_obj[key+self.slices]
        else:
            v = self.slice_obj[(key,)+self.slices]
        return v[...,self.boolindex]

class Workflow:
    """
    Indexes and maintains the workflow as a sequence of named stages.
    
    This class manages the workflow stages, including assigning, validating,
    and iterating over the stages.
    """

    def __init__(self, default_stages: List[str]):
        """
        Initialize a Workflow instance.
        
        Parameters
        ----------
        default_stages : List[str]
            List of all available workflow stages in order
        """
        self.default_stages = default_stages
        self.idx = {s:i for i, s in enumerate(default_stages)}
        self.snapshot_from = None

    def stage_idx(self, s: str) -> int:
        """
        Get the index of a stage by name.
        
        Parameters
        ----------
        s : str
            Name of the stage
        
        Returns
        -------
        int
            Index of the stage
        
        Raises
        ------
        ValueError
            If the stage name is unknown
        """
        try:
            return self.idx[s]
        except KeyError:
            raise ValueError(f'Unknown workflow stage: "{s}". '
                             f'Valid workflow stages are: {self.default_stages}.')

    def assign_all(self) -> None:
        """Assign all available stages to the workflow."""
        self.workflow = self.default_stages

    def assign_fromto(self, stage_from: Optional[str], stage_to: Optional[str]) -> None:
        """
        Assign a range of stages to the workflow.
        
        Parameters
        ----------
        stage_from : str or None
            Start stage (None for beginning)
        stage_to : str or None
            End stage (None for end)
        
        Raises
        ------
        KeyError
            If a stage name is unknown
        """
        try:
            wf1 = self.stage_idx(stage_from) if stage_from else 0
            wf2 = self.stage_idx(stage_to)   if stage_to   else -1
        except KeyError as e:
            die('Unknown stage: {}', e.args[0])

        self.workflow = self.default_stages[wf1:wf2+1]
        if wf1 > 0:
            self.snapshot_from = self.default_stages[wf1-1]

    def assign_list(self, stages: List[str]) -> None:
        try:
            workflow = [self.stage_idx(s) for s in stages]
        except KeyError as e:
            die('Unknown stage: {}', e.args[0])

        gaps = [i for i in range(1, len(workflow))
                if workflow[i-1]+1 != workflow[i]]
        if len(gaps) == 1:
            before = workflow[:gaps[0]]
            after = workflow[gaps[0]]
            if before in ([0], [0,1]) and after >= 2:
                self.snapshot_from = self.default_stages[after-1]
                warn('Partially supported non-continuous workflow. Snapshot '
                     'will be loaded from stage {}. Success is not '
                     'guaranteed.', self.snapshot_from)
                gaps = None
        else:
            if workflow[0] > 0:
                self.snapshot_from = self.default_stages[workflow[0]-1]

        if gaps:
            # Apart from supported case above
            die('Unsupported non-contiguous workflow! Selected stages {}. '
                'Complete workflow: {}.', stages, self.default_stages)

        self.workflow = [self.default_stages[si] for si in workflow]

    def __iter__(self):
        return iter(self.workflow)
