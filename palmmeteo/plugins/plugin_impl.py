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

from abc import ABC, abstractmethod
from pluggy import HookimplMarker

# Create a hookimpl marker for our package
hookimpl = HookimplMarker("palmmeteo")


class Plugin(ABC):
    """
    Base class for plugins

    The objects are not persistent across multiple runs, so their members (if
    any) should be created by the constructor and any stage should not expect
    members to be created by the preceding stages. Use rt to store persistent
    data.
    """

    @hookimpl
    def check_config(self):
        """(Load and) validate plugin-related configuration.

        Any plugin can optionally implement the check_config method for
        validating configuration. It is not required, so the method is not
        abstract.
        """
        pass


class ImportPluginMixin(Plugin):
    """
    Base class mixin for plugins importing data.
    Registers 'import_data' method as a handler for event 'import_data'.

    Abstract methods required to be implemented by derived classes:
        import_data
    """

    @abstractmethod
    @hookimpl
    def import_data(self, **kwargs):
        pass


class HInterpPluginMixin(Plugin):
    """
    Base class mixin for plugins importing data.
    Registers 'interpolate_horiz' method as a handler for event 'hinterp'.

    Abstract methods required to be implemented by derived classes:
        interpolate_horiz
    """

    @abstractmethod
    @hookimpl
    def interpolate_horiz(self, **kwargs):
        pass


class VInterpPluginMixin(Plugin):
    """
    Base class mixin for plugins importing data.
    Registers 'interpolate_vert' method as a handler for event 'vinterp'.

    Abstract methods required to be implemented by derived classes:
        interpolate_vert
    """

    @abstractmethod
    @hookimpl
    def interpolate_vert(self, **kwargs):
        pass


class SetupPluginMixin(Plugin):
    """
    Base class mixin for setup plugins.
    Registers 'setup_model' method as a handler for event 'setup_model'.

    Abstract methods required to be implemented by derived classes:
        setup_model
    """

    @abstractmethod
    @hookimpl
    def setup_model(self, **kwargs):
        pass


class WritePluginMixin(Plugin):
    """
    Base class mixin for writer plugins.
    Registers 'write_data' method as a handler for event 'write'.

    Abstract methods required to be implemented by derived classes:
        write_data
    """

    @abstractmethod
    @hookimpl
    def write_data(self, **kwargs):
        pass


def plugin_factory(plugin, *args, **kwargs):
    import importlib
    try:
        mod_name, cls_name = plugin.rsplit('.', 1)
        mod_obj = importlib.import_module(mod_name)
        cls_obj = getattr(mod_obj, cls_name)
    except ValueError:
        import sys
        cls_obj = getattr(sys.modules[__name__], plugin)

    plugin_instance = cls_obj(*args, **kwargs)

    return plugin_instance
