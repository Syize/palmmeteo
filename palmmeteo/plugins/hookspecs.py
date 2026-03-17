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

from pluggy import HookspecMarker

# Create a hookspec marker for our package
hookspec = HookspecMarker("palmmeteo")


@hookspec
def check_config() -> None:
    """(Load and) validate plugin-related configuration.

    Any plugin can optionally implement the check_config method for
    validating configuration. It is not required.
    """
    pass


@hookspec
def import_data(**kwargs) -> None:
    """Import data from external sources.

    This method is called by the 'import_data' event.
    """
    pass


@hookspec
def interpolate_horiz(**kwargs) -> None:
    """Interpolate data horizontally.

    This method is called by the 'hinterp' event.
    """
    pass


@hookspec
def interpolate_vert(**kwargs) -> None:
    """Interpolate data vertically.

    This method is called by the 'vinterp' event.
    """
    pass


@hookspec
def setup_model(**kwargs) -> None:
    """Setup the model.

    This method is called by the 'setup_model' event.
    """
    pass


@hookspec
def write_data(**kwargs) -> None:
    """Write data to output files.

    This method is called by the 'write' event.
    """
    pass
