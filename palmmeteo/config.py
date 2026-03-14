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

import os
import datetime
from collections import defaultdict
import importlib.resources
import pkgutil
from typing import Any, Dict, List, Optional, Iterator

from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from .logging import die, warn, log, verbose
from .workflow import Workflow

class ConfigError(Exception):
    """
    Exception raised for configuration errors.

    This exception class provides detailed information about configuration
    errors, including the error description, section, and key where the
    error occurred.
    """
    
    def __init__(self, desc: str, section: Optional['ConfigObj'] = None, key: Optional[str] = None):
        """
        Initialize a ConfigError instance.

        Parameters
        ----------
        desc : str
            Error description
        section : ConfigObj, optional
            Configuration section where the error occurred
        key : str, optional
            Configuration key where the error occurred
        """
        self.desc = desc
        self.section = section
        self.key = key

        # Build message
        s = ['Configuration error: ', desc]
        if section:
            s.extend([', item: ', ':'.join(section._get_path()+[key])])
            try:
                v = section._settings[key]
            except KeyError:
                s.append(', missing value')
            else:
                s.extend([', value=', str(v)])
        s.append('.')
        self.msg = ''.join(s)

    def __str__(self):
        return self.msg

class ConfigObj(object):
    """
    A recursive object within a hierarchical configuration, representing
    a (sub)section as a dictionary from the YAML configuration file. Child
    nodes may be accessed both by the dot notation (section.setting) and the
    item notation (section['setting']).
    """
    # We use __slots__ because we intend to hardly limit (and control) instance
    # members, so that we do not break many potential names of actual settings
    # that are accessed using the dot notation. For the same reason, member and
    # method names (mostly used internally anyway) start with an underscore.
    __slots__ = ['_parent', '_name', '_settings']

    def __init__(self, parent: Optional['ConfigObj'] = None, name: Optional[str] = None):
        """
        Initialize a ConfigObj instance.

        Parameters
        ----------
        parent : ConfigObj, optional
            Parent configuration object
        name : str, optional
            Name of this configuration section
        """
        self._parent = parent
        self._name = name
        self._settings: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        try:
            return self._settings[name]
        except KeyError:
            raise AttributeError('Attribute {} not found. Possibly a missing '
                    'configuration setting in section {}.'.format(name,
                        ':'.join(self._get_path())))

    def __getitem__(self, key: str) -> Any:
        try:
            return self._settings[key]
        except KeyError:
            raise KeyError('Key {} not found. Possibly a missing configuration '
                    'setting in section {}.'.format(key,
                        ':'.join(self._get_path())))

    def __contains__(self, key: str) -> bool:
        return key in self._settings

    def __iter__(self) -> Iterator[Any]:
        return iter(self._settings.items())

    def _ingest_dict(self, d: Dict[str, Any], overwrite: bool = True, 
                   extend: bool = False, check_exist: bool = False) -> None:
        """
        Ingest a dictionary into the configuration object.

        Parameters
        ----------
        d : dict
            Dictionary to ingest
        overwrite : bool, optional
            Whether to overwrite existing values, by default True
        extend : bool, optional
            Whether to extend lists instead of replacing them, by default False
        check_exist : bool, optional
            Whether to check if settings exist before overwriting, by default False
        """
        for k, v in d.items():
            if isinstance(v, ConfigObj):
                # we are actually ingesting a subtree - replace by its dict
                v = v._settings

            if isinstance(v, dict):
                # For a dictionary (top-level or with only dictionaries above,
                # i.e. a subsection), we recurse
                do_check_exist = check_exist
                try:
                    vl = self._settings[k]
                except KeyError:
                    # not yet present: create a new empty child node
                    vl = ConfigObj(self, k)
                    self._settings[k] = vl
                    if self._settings.get('__user_expandable__', False):
                        do_check_exist = False
                try:
                    vl._ingest_dict(v, overwrite, extend, do_check_exist)
                except AttributeError:
                    raise ConfigError('Trying to replace a non-dictionary '
                            'setting with a dictionary', self, k)
            elif extend and isinstance(v, list):
                # We extend lists if requested
                vl = self._settings.setdefault(k, [])
                try:
                    vl.extend(v)
                except AttributeError:
                    raise ConfigError('Trying to extend a non-list setting with '
                            'a list', self, k)
            elif v is None and isinstance(self._settings.get(k), ConfigObj):
                # This is a special case: we are replacing an existing section
                # with None. That most probably means that the user has
                # presented an empty section (possibly with all values
                # commented out). In that case, we do not want to erase that
                # section. To actually erase a whole section, the user can
                # still present empty dictionary using the following syntax:
                # section_name: {}
                pass
            else:
                # Non-extended lists and all other objects are considered as
                # values and they are copied as-is (including their subtrees if
                # present). Non-null values are overwritten only if
                # overwrite=True.
                if overwrite:
                    if check_exist and k not in self._settings:
                        warn('WARNING: ignoring an unknown setting {}={}.',
                                ':'.join(self._get_path()+[k]), v)
                    self._settings[k] = v
                else:
                    if self._settings.get(k, None) is None:
                        self._settings[k] = v

    def _ingest_module_config(self, modname: str) -> None:
        """
        Locates the initial configuration file config_init.yaml within module
        code and ingests it.
        """
        fpath = importlib.resources.files(modname).joinpath('config_init.yaml')

        if not fpath.is_file():
            die('Cannot find initial configuration for package {}! Expected at {}.',
                modname, fpath)

        verbose('Loading {} configuration from {}', modname, fpath)
        with fpath.open('r') as f:
            cfg._ingest_dict(load(f, Loader=SafeLoader))

    def _get_path(self):
        if self._parent is None:
            return []
        path = self._parent._get_path()
        path.append(self._name)
        return path


duration_units = {
        'd': 'days',
        'h': 'hours',
        'm': 'minutes',
        's': 'seconds',
        }

def parse_duration(section: 'ConfigObj', item: str, value: Optional[str] = None) -> datetime.timedelta:
    def err():
        raise ConfigError('Bad specification of duration. The correct format is '
                '{num} {unit} [{num} {unit} ...], where {unit} is one of d, h, '
                'm, s. Example: "1 m 3.2 s".', section, item)

    if value is None:
        try:
            s = section[item]
        except KeyError:
            err()
    else:
        s = value

    words = s.split()
    n = len(words)
    if n % 2:
        err()

    d = defaultdict(int)
    for i in range(0, n, 2):
        ns, unit = words[i:i+2]
        try:
            num = int(ns)
        except ValueError:
            try:
                num = float(ns)
            except ValueError:
                err()
        try:
            u = duration_units[unit]
        except KeyError:
            err()
        d[u] += num

    return datetime.timedelta(**d)


def load_config(argv: Any) -> Workflow:
    """
    Loads all configuration.

    Configuration is loaded in this order:
    1) initial configuration values
    2) configfile
    3) command-line options
    Each step may overwrite values from previous steps.
    """
    global cfg

    log('Loading configuration')

    # Load initial configuration for core palmmeteo
    cfg._ingest_module_config('palmmeteo')

    # Standard plugins are mandatory and loaded first
    cfg._ingest_module_config('palmmeteo_stdplugins')

    # Load initial configuration for plugins by finding all other modules that
    # start with palmmeteo_
    for modfinder, modname, ispkg in pkgutil.iter_modules():
        if modname.startswith('palmmeteo_') and modname != 'palmmeteo_stdplugins':
            cfg._ingest_module_config(modname)

    # load settings from selected configfiles
    for fn_cfg in argv.config:
        with open(fn_cfg, 'r') as config_file:
            cfg._ingest_dict(load(config_file, Loader=SafeLoader),
                    check_exist=True)

    # apply settings for selected tasks
    for task in cfg.tasks:
        try:
            task_set = cfg.task_config._settings[task]
        except KeyError:
            die('Unknown task: "{}". Available tasks are: {}', task,
                    ', '.join(cfg.task_config._settings.keys()))

        if task_set.set:
            cfg._ingest_dict(task_set.set._settings, overwrite=False, extend=False)
        if task_set.extend:
            cfg._ingest_dict(task_set.extend._settings, overwrite=False, extend=True)

    # load extra settings from commandline
    if argv.verbosity_arg is not None:
        cfg._settings['verbosity'] = argv.verbosity_arg

    # process workflow
    workflow = Workflow(cfg.full_workflow)

    if argv.workflow:
        workflow.assign_list(argv.workflow)
    elif argv.workflow_from or argv.workflow_to:
        workflow.assign_fromto(argv.workflow_from, argv.workflow_to)
    elif cfg.workflow:
        workflow.assign_list(cfg.workflow)
    else:
        workflow.assign_all()

    # Basic verification
    if not cfg.case:
        raise ConfigError('Case name must be specified', cfg, 'case')

    return workflow


cfg = ConfigObj()
