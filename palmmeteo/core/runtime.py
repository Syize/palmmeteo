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
import os
import pickle
from typing import Any, Optional

from .. import signature
from ..logging import die, warn, log, verbose
from .config import cfg, parse_duration, ConfigObj
from ..exceptions import ConfigurationError

zstd = None

def myopen(fpath: str, *args: Any, **kwargs: Any) -> Any:
    """
    Open a file, supporting zstandard compression.

    Parameters
    ----------
    fpath : str
        Path to the file to open
    *args : Any
        Positional arguments to pass to the underlying open function
    **kwargs : Any
        Keyword arguments to pass to the underlying open function

    Returns
    -------
    file object
        Opened file object

    Notes
    -----
    If the file path ends with .zst, it will be decompressed using zstandard
    compression. The zstd module is dynamically imported when needed.
    """
    global zstd

    if fpath.endswith('.zst'):
        if zstd is None:
            try:
                from compression import zstd
            except ImportError:
                import pyzstd as zstd
        return zstd.open(fpath, *args, **kwargs)
    else:
        return open(fpath, *args, **kwargs)

class RuntimeObj:
    """
    An object for holding runtime-related values that may be nested.

    This class provides a simple way to store and access runtime data in
    a hierarchical structure. It supports saving and loading snapshots of
    its state using pickle serialization.
    """

    def _get_child(self, child_name: str) -> 'RuntimeObj':
        """
        Get or create a child RuntimeObj instance.

        Parameters
        ----------
        child_name : str
            Name of the child object to get or create

        Returns
        -------
        RuntimeObj
            Child RuntimeObj instance
        """
        try:
            return self.__dict__[child_name]
        except KeyError:
            newchild = self.__class__()
            self.__dict__[child_name] = newchild
            return newchild

    def _save(self, fpath: str) -> None:
        """
        Save the current state of the RuntimeObj to a file.

        Parameters
        ----------
        fpath : str
            Path to the file where the snapshot should be saved
        """
        log('Saving snapshot to {}', fpath)
        with myopen(fpath, 'wb') as f:
            p = pickle.Pickler(f, protocol=cfg.intermediate_files.pickle_protocol,
                    fix_imports=False)
            p.dump(signature)
            p.dump(self.__dict__)
            if rt.debug.snapshots:
                for k, v in self.__dict__.items():
                    if hasattr(v, 'nbytes'):
                        verbose('{}:\t{} bytes (np).', k, v.nbytes)
                    else:
                        try:
                            l = len(v)
                        except:
                            verbose('{}:\t{} bytes (sys).', k, sys.getsizeof(v))
                        else:
                            verbose('{}:\tlength {}, {} bytes (sys).', k, l, sys.getsizeof(v))
        verbose('Snapshot saved.')

    def _load(self, fpath: str) -> None:
        """
        Load a saved snapshot of the RuntimeObj from a file.

        Parameters
        ----------
        fpath : str
            Path to the file containing the saved snapshot
        """
        log('Loading snapshot from {}', fpath)
        with myopen(fpath, 'rb') as f:
            p = pickle.Unpickler(f, fix_imports=False)
            sig_loaded = p.load()
            loaded = p.load()
        if sig_loaded == signature:
            verbose('Loaded snapshot version: {}', sig_loaded)
        else:
            warn('Loaded snapshot version "{}" does not match current '
                 'version "{}", errors may follow!', sig_loaded, signature)
        assert isinstance(loaded, dict)
        self.__dict__.update(loaded)

def basic_init(rt: RuntimeObj) -> None:
    """
    Performs initialization of basic values from configuration.

    Parameters
    ----------
    rt : RuntimeObj
        Runtime object to initialize

    Notes
    -----
    This function initializes several key runtime values from the
    configuration, including:
    - Simulation times (timestep, length, radiation timestep)
    - Paths and path strings
    - Domain properties (nested domain, stretching)
    - Debugging settings
    """
    # Times
    simulation = rt._get_child('simulation')
    simulation.timestep = parse_duration(cfg.simulation, 'timestep')
    simulation.length = parse_duration(cfg.simulation, 'length')
    if cfg.radiation.timestep == 'auto':
        rt.timestep_rad = None
    else:
        rt.timestep_rad = parse_duration(cfg.radiation, 'timestep')
    simulation.spinup_rad = parse_duration(cfg.radiation, 'spinup_length')

    # Paths
    rt.path_strings = {}
    for key, func in cfg.path_strings:
        try:
            code = compile(func, f'<path_string_{key}>', 'eval')
        except SyntaxError as e:
            raise ConfigurationError(f'Syntax error in definition of the path string "{key}": {e}', section='path_strings', key=key)
        try:
            val = eval(code, cfg._settings)
        except Exception as e:
            raise ConfigurationError(f'Error while evaluating the path string "{key}": {e}', section='path_strings', key=key)
        rt.path_strings[key] = val

    paths = rt._get_child('paths')
    paths.base = cfg.paths.base.format(**rt.path_strings)
    for sect_name, sect_cfg in cfg.paths:
        if isinstance(sect_cfg, ConfigObj):
            path_sect = paths._get_child(sect_name)
            for key, val in sect_cfg:
                if isinstance(val, str):
                    setattr(path_sect, key,
                        os.path.join(paths.base, val.format(**rt.path_strings)))

    # Domain
    rt.nested_domain = (cfg.dnum > 1)
    rt.stretching = (cfg.domain.dz_stretch_factor != 1.0)

    # Debugging
    debug = rt._get_child('debug')
    isall = cfg.debug.all
    for dname, don in cfg.debug:
        setattr(debug, dname, isall or don)

# Global runtime object
rt = RuntimeObj()
