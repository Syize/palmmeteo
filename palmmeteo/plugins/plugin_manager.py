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

from pluggy import PluginManager
from . import hookspecs

# Create a PluginManager instance for our package
pm = PluginManager("palmmeteo")

# Register hooks specifications from the hookspecs module
pm.add_hookspecs(hookspecs)

# Event to hook mapping
event_hooks = {
    'check_config': 'check_config',
    'import_data': 'import_data',
    'hinterp': 'interpolate_horiz',
    'vinterp': 'interpolate_vert',
    'setup_model': 'setup_model',
    'write': 'write_data'
}


def initialize_plugins(plugins):
    """
    Initialize and register plugins.

    Parameters
    ----------
    plugins : list
        List of plugin class names to initialize

    Returns
    -------
    list
        List of initialized plugin instances
    """
    from .plugin_impl import plugin_factory

    instances = []
    for plugin in plugins:
        instance = plugin_factory(plugin)
        pm.register(instance)
        instances.append(instance)

    return instances


def execute_event(event, **kwargs):
    """
    Execute an event by calling all registered hooks for that event.

    Parameters
    ----------
    event : str
        Event name to execute
    **kwargs : dict
        Additional keyword arguments to pass to the hooks

    Returns
    -------
    list
        Results from all hooks
    """
    hook_name = event_hooks.get(event)
    if hook_name:
        return getattr(pm.hook, hook_name)(**kwargs)
    else:
        raise ValueError(f"Unknown event: {event}")
