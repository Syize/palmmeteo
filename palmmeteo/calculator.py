"""
calculator.py - Quantity calculation and formula evaluation

This module contains classes for calculating quantities from formulas and
handling loaded variables, preprocessors, and validations.
"""

from .units import LoadedQuantity, UnitConverter, InputUnitsInfo
from .exceptions import ConfigurationError, DataError, CalculationError

class QuantityCalculator:
    def __init__(self, quantities, var_defs, preprocessors, regridder):
        self.regridder = regridder
        self.loaded_vars = set()
        self.preprocessors = {}
        self.validations = {}
        self.quantities = []

        for qname in quantities:
            vdef = self._get_vdef(var_defs, qname)
            q = LoadedQuantity()
            q.name = qname

            self.loaded_vars.update(vdef.loaded_vars)
            if len(vdef.loaded_vars) == 1 and 'formula' not in vdef:
                # When we have exactly 1 loaded variable and we do not define
                # an explicit formula, we assume that the formula is identity
                # for that variable and the unit is taken from the input
                # variable unless specified otherwise.
                q.formula = vdef.loaded_vars[0]
                q.unit = getattr(vdef, 'unit', None)
                                #None = taken later from loaded variable
            else:
                q.formula = vdef.formula
                q.unit = vdef.unit

            for pp in getattr(vdef, 'preprocessors', []):
                if pp not in self.preprocessors:
                    try:
                        prs = preprocessors[pp]
                    except KeyError:
                        raise ConfigurationError('Requested input preprocessor {} not found in configured variable definitions'.format(pp))
                    try:
                        self.preprocessors[pp] = compile(prs,
                                '<quantity_preprocessor_{}>'.format(pp), 'exec')
                    except SyntaxError:
                        raise ConfigurationError('Syntax error in definition of the input preprocessor {}: "{}"'.format(pp, prs))

            for val in getattr(vdef, 'validations', []):
                if val not in self.validations:
                    try:
                        self.validations[val] = compile(val,
                                '<quantity_validation>', 'eval')
                    except SyntaxError:
                        raise ConfigurationError('Syntax error in definition of the input validation: "{}"'.format(val))

            q.attrs = {}
            if 'molar_mass' in vdef:
                q.attrs['molar_mass'] = vdef.molar_mass
            for flag in getattr(vdef, 'flags', []):
                q.attrs[flag] = __import__('numpy').int8(1)

            try:
                q.code = compile(q.formula, '<quantity_formula_{}>'.format(qname), 'eval')
            except SyntaxError:
                raise ConfigurationError('Syntax error in definition of the quantity {} formula: "{}"'.format(qname, q.formula))
            self.quantities.append(q)

    @staticmethod
    def _get_vdef(var_defs, qname):
        try:
            return var_defs[qname]
        except KeyError:
            raise ConfigurationError('Requested quantity {} not found in configured quantity definitions'.format(qname))

    @classmethod
    def get_loaded_vars(cls, quantities, var_defs):
        return set().union(*(
            cls._get_vdef(var_defs, qname).loaded_vars
            for qname in quantities))

    @staticmethod
    def new_timestep():
        return {'_units': InputUnitsInfo()}

    def load_timestep_vars(self, f, tindex, tsdata):
        complete = True
        units = tsdata['_units']

        for vn in self.loaded_vars:
            if vn in tsdata:
                if vn in f.variables:
                    from .logging import die
                    die('Error: duplicate input variable {}.', vn)
            else:
                try:
                    var = f.variables[vn]
                except KeyError:
                    complete = False
                    continue

                tsdata[vn] = self.regridder.loader(var)[tindex,...]
                setattr(units, vn, var.units)

        return complete

    def validate_timestep(self, tsdata):
        for vs, val in self.validations.items():
            try:
                if not eval(val, tsdata):
                    raise DataError(f'Input validation {vs} failed!')
            except Exception as e:
                raise CalculationError(f'Validation {vs} failed: {e}')

    def calc_timestep_species(self, tsdata):
        for pp in self.preprocessors.values():
            try:
                exec(pp, tsdata)
            except Exception as e:
                raise CalculationError(f'Preprocessor execution failed: {e}')

        for q in self.quantities:
            try:
                value = eval(q.code, tsdata)
                unit = q.unit

            # Assign default unit with directly loaded variables
            if unit is None:
                unit = getattr(tsdata['_units'], q.formula)

            # Check for necessary unit conversion
            value, unit = UnitConverter.convert(q.name, value, unit)

            yield q.name, value, unit, q.attrs
