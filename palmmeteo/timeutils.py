"""
timeutils.py - Time handling utilities

This module contains utility functions for handling time and timesteps.
"""

import datetime
from dataclasses import dataclass
from typing import Callable

utc = datetime.timezone.utc
midnight = datetime.time(0)

utcdefault: Callable[[datetime.datetime], datetime.datetime] = lambda dt: dt.replace(tzinfo=utc) if dt.tzinfo is None else dt
midnight_of: Callable[[datetime.datetime], datetime.datetime] = lambda dt: datetime.datetime.combine(dt.date(), midnight, dt.tzinfo)

class NotWholeTimestep(ValueError):
    """Exception raised when a timestep is not a whole multiple of the reference timestep."""
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
