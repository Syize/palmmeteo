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

from ..logging import die, warn, log, verbose
from ..workflow import Workflow
from ..exceptions import ConfigurationError
from .config_model import ConfigObj


duration_units = {
        'd': 'days',
        'h': 'hours',
        'm': 'minutes',
        's': 'seconds',
        }

def parse_duration(section: 'ConfigObj', item: str, value: Optional[str] = None) -> datetime.timedelta:
    def err():
        raise ConfigurationError('Bad specification of duration. The correct format is '
                '{num} {unit} [{num} {unit} ...], where {unit} is one of d, h, '
                'm, s. Example: "1 m 3.2 s".', section=':'.join(section._get_path()), key=item)

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
            task_set = cfg.task_config[task]
        except KeyError:
            die('Unknown task: "{}". Available tasks are: {}', task,
                    ', '.join(cfg.task_config.root.keys()))

        if task_set.set:
            cfg._ingest_dict(task_set.set.root, overwrite=False, extend=False)
        if task_set.extend:
            cfg._ingest_dict(task_set.extend.root, overwrite=False, extend=True)

    # load extra settings from commandline
    if argv.verbosity_arg is not None:
        cfg.root['verbosity'] = argv.verbosity_arg

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
        raise ConfigurationError('Case name must be specified', section='', key='case')

    return workflow


cfg = ConfigObj(__root__={})
