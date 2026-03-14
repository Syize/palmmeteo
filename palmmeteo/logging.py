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

import sys
from time import strftime
from typing import Any

__all__ = ['die', 'warn', 'log', 'verbose', 'configure_log']

dtf = '%Y-%m-%d %H:%M:%S '
log_output = sys.stdout.write
error_output = sys.stderr.write

def die(s: str, *args: Any, **kwargs: Any) -> None:
    """
    Write message to error output and exit with status 1.

    Parameters
    ----------
    s : str
        Message string to write (supports format string syntax)
    *args : Any
        Positional arguments for string formatting
    **kwargs : Any
        Keyword arguments for string formatting

    Examples
    --------
    >>> die("Error: {} not found", "file.txt")
    Error: file.txt not found
    """
    if args or kwargs:
        error_output(s.format(*args, **kwargs) + '\n')
    else:
        error_output(s + '\n')
    sys.exit(1)


def warn(s: str, *args: Any, **kwargs: Any) -> None:
    """
    Write message to error output.

    Parameters
    ----------
    s : str
        Message string to write (supports format string syntax)
    *args : Any
        Positional arguments for string formatting
    **kwargs : Any
        Keyword arguments for string formatting

    Examples
    --------
    >>> warn("Warning: File {} may be corrupted", "data.nc")
    Warning: File data.nc may be corrupted
    """
    if args or kwargs:
        error_output(s.format(*args, **kwargs) + '\n')
    else:
        error_output(s + '\n')

class LoggingLevel:
    """
    Class representing a logging level with state and datetime configuration.
    """
    
    def __init__(self, is_on: bool, use_dt: bool = False) -> None:
        """
        Initialize a LoggingLevel instance.

        Parameters
        ----------
        is_on : bool
            Whether the logging level is active
        use_dt : bool, optional
            Whether to include datetime in log messages, by default False
        """
        self.is_on = is_on
        self.use_dt = use_dt

    def __call__(self, s: str, *args: Any, **kwargs: Any) -> None:
        """
        Write logging or debugging message with optional datetime if configured to do so.

        Parameters
        ----------
        s : str
            Message string to write (supports format string syntax)
        *args : Any
            Positional arguments for string formatting
        **kwargs : Any
            Keyword arguments for string formatting
        """
        if not self.is_on:
            return

        if args or kwargs:
            ss = s.format(*args, **kwargs)
        else:
            ss = s

        if self.use_dt:
            log_output(strftime(dtf) + ss + '\n')
        else:
            log_output(ss + '\n')

    def __bool__(self) -> bool:
        """
        Return whether the logging level is active.
        """
        return self.is_on

log = LoggingLevel(True)
verbose = LoggingLevel(False)

def configure_log(verbosity: int, log_datetime: bool = False) -> None:
    """
    Configure logging levels based on verbosity and datetime settings.

    Parameters
    ----------
    verbosity : int
        Verbosity level (0: silent, 1: normal, 2: verbose)
    log_datetime : bool, optional
        Whether to include datetime in log messages, by default False
    """
    log.__init__(verbosity >= 1, log_datetime)
    verbose.__init__(verbosity >= 2, log_datetime)
