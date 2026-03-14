"""
constants.py - Numeric and time-related constants

This module contains common numeric constants used throughout the PALM-METEO
codebase, including mathematical constants, time-related constants, and
other general-purpose values.
"""

import numpy as np
import datetime

# Numeric constants
ax_ = np.newaxis
rad = np.pi / 180.

# Time-related constants
td0 = datetime.timedelta(0)
utc = datetime.timezone.utc
midnight = datetime.time(0)

utcdefault = lambda dt: dt.replace(tzinfo=utc) if dt.tzinfo is None else dt
midnight_of = lambda dt: datetime.datetime.combine(dt.date(), midnight, dt.tzinfo)

# Other
eps_grid = 1e-3 #Acceptable rounding error for grid points
fext_re = __import__('re').compile(r'\.(\d{3})$')
where_range = lambda mask: (np.argmax(mask), len(mask)-np.argmax(mask[::-1]))
