"""
time.py - Time cycle and horizon selection

This module contains classes for handling assimilation cycles and
forecast horizon selections based on configuration.
"""

import math
import datetime
import numpy as np
import netCDF4

from .config import parse_duration
from .exceptions import ConfigurationError
from .timeutils import midnight_of, NotWholeTimestep, utc, utcdefault
from .logging import verbose
from .runtime import rt

class AssimCycle:
    """List of selected assimilation cycles based on configuration"""

    def __init__(self, cfgsect):
        cint = cfgsect.cycles_used
        cref = cfgsect.reference_cycle

        if cint == 'all':
            self.cycle_int = False
            if cref:
                raise ConfigurationError('Reference cycle cannot be specified for '
                        'cycles_used=all', section='', key='reference_cycle')
            self.is_selected = self._is_selected_all
        else:
            if cref:
                self.cycle_ref = utcdefault(cref)
            else:
                # Use 00:00 UTC of the first day of simulation
                self.cycle_ref = midnight_of(rt.simulation.start_time)

            if cint == 'single':
                self.cycle_int = None
                self.is_selected = self._is_selected_single
                verbose('Using forecast/assimilaton cycle {}', self.cycle_ref)
            else:
                self.cycle_int = parse_duration(cfgsect, 'reference_cycle', cint)
                self.is_selected = self._is_selected_interval
                verbose('Using forecast/assimilation cycles every {} '
                        '(with reference to {})', self.cycle_int, self.cycle_ref)

    def _is_selected_interval(self, cycle_dt):
        """Test whether the cycle is among the selected cycles"""
        return not (cycle_dt - self.cycle_ref) % self.cycle_int # remainder is timedelta(0)

    def _is_selected_single(self, cycle_dt):
        """Test whether the cycle is among the selected cycles"""
        return cycle_dt == self.cycle_ref

    def _is_selected_all(self, cycle_dt):
        """Test whether the cycle is among the selected cycles"""
        return True

class HorizonSelection:
    """
    Represents a continous selection of forecast horizons for
    a given selection of cycles (AssimCycle)
    """
    def __init__(self, cycles, earliest_horizon, idx_start=None, idx_stop=None,
                 tindex=None, idx_rad=False):
        self.cycles = cycles
        self.horiz_first = earliest_horizon
        if not cycles.cycle_int:
            self.horiz_last = datetime.timedelta(days=999999)
        else:
            self.horiz_last = earliest_horizon + cycles.cycle_int - rt.simulation.timestep

        if idx_rad:
            self.idx0 = (math.floor(-rt.simulation.spinup_rad / rt.timestep_rad)
                         if idx_start is None else idx_start)
            self.idx1 = (math.ceil((rt.simulation.end_time_rad - rt.simulation.start_time) / rt.timestep_rad) + 1
                         if idx_stop is None else idx_stop)
        else:
            self.idx0 = 0 if idx_start is None else idx_start
            self.idx1 = rt.nt if idx_stop is None else idx_stop
        self.tindex = rt.tindex if tindex is None else tindex

    @classmethod
    def from_cfg(cls, cfgsect, idx_start=None, idx_stop=None, tindex=None, idx_rad=False):
        cycles = AssimCycle(cfgsect)
        hor0 = parse_duration(cfgsect, 'earliest_horizon')
        return cls(cycles, hor0, idx_start=idx_start, idx_stop=idx_stop,
                   tindex=tindex, idx_rad=idx_rad)

    def get_idx(self, horizon, dt_idx):
        if not self.idx0 <= dt_idx < self.idx1:
            return False
        if not self.horiz_first <= horizon <= self.horiz_last:
            return False
        return dt_idx - self.idx0

    def locate(self, cycle, horizon=None, dt=None):
        if not self.cycles.is_selected(cycle):
            verbose('Cycle {} not included', cycle)
            return False

        try:
            dt_idx = self.tindex(cycle+horizon if dt is None else dt)
        except NotWholeTimestep:
            return False

        return self.get_idx(dt-cycle if horizon is None else horizon, dt_idx)

    def dt_from_idx(self, idx):
        dt = rt.simulation.start_time + rt.simulation.timestep*(idx+self.idx0)
        match self.cycles.cycle_int:
            case False:
                # all cycles accepted => cycle unknown
                return None, None, dt
            case None:
                # single cycle
                return self.cycles.cycle_ref, dt - self.cycles.cycle_ref, dt
            case interval:
                # cycle interval
                horizon = (dt - self.cycles.cycle_ref - self.horiz_first) % interval
                horizon += self.horiz_first
                cycle = dt - horizon
                return cycle, horizon, dt

class NCDates:
    """
    Represents dates found in an NetCDF file with CF conventions and their
    match (intersection) with given HorizonSelection.
    """
    def __init__(self, ncvar):
        ntimes, = ncvar.shape
        mytimes = np.zeros((ntimes+1,), dtype=ncvar.dtype)
        mytimes[1:] = ncvar[:]
        dts = netCDF4.num2date(mytimes, ncvar.units, ncvar.calendar,
                               only_use_cftime_datetimes=False,
                               only_use_python_datetimes=True)
        if dts[0].tzinfo is None:
            dts = [dt.replace(tzinfo=utc) for dt in dts]
        self.origin = dts[0]
        self.times = dts[1:]

    @classmethod
    def from_origin(cls, dt_origin, units, times):
        obj = cls.__new__(cls)
        obj.origin = utcdefault(dt_origin)
        obj.times = obj.origin + times * datetime.timedelta(**{units: 1})
        return obj

    def match_hselect(self, hselect):
        """Find file time indices (if any) that match the given HorizonSelection"""

        self.matching = m = []
        for file_idx, dt in enumerate(self.times):
            sel_idx = hselect.locate(self.origin, dt=dt)
            if sel_idx is not False:
                m.append((file_idx, sel_idx))
        return m #can be truth-tested for non-emptiness
