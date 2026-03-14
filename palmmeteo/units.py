"""
units.py - Unit conversion and handling

This module contains classes and functions for unit conversion and handling
input units information.
"""

import re

from .config import cfg

class UnitConverter:
    loaded = None

    def __init__(self):
       self.re_ppmv = re.compile(cfg.chem_units.regexes.ppmv)
       self.re_ppbv = re.compile(cfg.chem_units.regexes.ppbv)
       self.re_ugm3 = re.compile(cfg.chem_units.regexes.ugm3)
       self.re_gm3  = re.compile(cfg.chem_units.regexes.gm3)
       self.re_kgm3 = re.compile(cfg.chem_units.regexes.kgm3)

    def convert_auto(self, name, value, unit):
        # volumetric fractional
        if self.re_ppmv.match(unit):
            from .logging import verbose
            verbose('Unit {} for variable {} understood as ppmv', unit, name)
            return value, cfg.chem_units.targets.ppmv
        if self.re_ppbv.match(unit):
            from .logging import verbose
            verbose('Converting {} from {} (understood as ppbv) to ppmv', name, unit)
            return value*1e-3, cfg.chem_units.targets.ppmv

        # mass per volume
        if self.re_ugm3.match(unit):
            from .logging import verbose
            verbose('Converting {} from {} (understood as ug/m3) to kg/m3', name, unit)
            return value*1e-9, cfg.chem_units.targets.kgm3
        if self.re_gm3.match(unit):
            from .logging import verbose
            verbose('Converting {} from {} (understood as g/m3) to kg/m3', name, unit)
            return value*1e-3, cfg.chem_units.targets.kgm3
        if self.re_kgm3.match(unit):
            from .logging import verbose
            verbose('Unit {} for variable {} understood as kg/m3', unit, name)
            return value, cfg.chem_units.targets.kgm3

        # default
        from .logging import warn
        warn('Unknown unit {} for variable {} - keeping.', unit, name)
        return value, unit

    @classmethod
    def convert(cls, name, value, unit):
        if cls.loaded is None:
            cls.loaded = cls()
        return cls.loaded.convert_auto(name, value, unit)

class InputUnitsInfo:
    """
    Container class for storing units information about input variables.
    """
    pass

class LoadedQuantity:
    """
    Represents a loaded quantity with its name, formula, code, unit, and attributes.
    """
    __slots__ = ['name', 'formula', 'code', 'unit', 'attrs']
