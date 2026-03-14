"""
io.py - Input gathering and handling

This module contains classes for gathering input variables for the import step,
checking for completeness, and handling vertical levels if they are not known
in advance.
"""

import numpy as np

from .netcdfutils import ensure_dimension

class InputGatherer:
    """
    Helps gather input variables for the import step and check for
    completeness. Also helps handle list of vertical levels if it is not known
    in advance. Only works on identically-shaped data - use more than one
    object if you have e.g. 2D + 3D variables.
    """
    def __init__(self, fout, varnames, nt, output_dims, dyn_levels=True,
                 copy_attrs=[]):
        self.fout = fout
        self.nt = nt
        self.varnames = varnames
        self.nv = len(varnames)
        self.idx_var = {k:i for i, k in enumerate(varnames)}
        self.output_dims = output_dims
        self.copy_attrs = copy_attrs
        ensure_dimension(fout, output_dims[0], nt) #time dimension

        self.dyn_levels = dyn_levels
        if dyn_levels:
            self.levels = []
            self.idx_lev = {}
            self.filled = []
            self.level_dimname = self.output_dims[1]
            fout.createDimension(self.level_dimname, None)
            self.extra_dims = output_dims[2:]
        else:
            self.filled = np.zeros((self.nt, self.nv), dtype=bool)
            self.extra_dims = output_dims[1:]

    def _get_level(self, level):
        nlev = len(self.levels)
        il = self.idx_lev.setdefault(level, nlev)
        if il == nlev:
            self.levels.append(level)
            self.filled.append(np.zeros((self.nt, self.nv), dtype=bool))
        return il

    def _get_var(self, varname, dt, shape, attrs):
        try:
            return self.fout.variables[varname]
        except KeyError:
            for dn, ds in zip(self.extra_dims, shape):
                ensure_dimension(self.fout, dn, ds)
            v = self.fout.createVariable(varname, dt, self.output_dims)
            if self.copy_attrs:
                if hasattr(attrs, 'getncattr'):
                    v.setncatts({a: attrs.getncattr(a) for a in self.copy_attrs})
                else:
                    v.setncatts({a: attrs[a] for a in self.copy_attrs})
            return v

    def add_single_lev(self, varname, it, level, data, attrs={}):
        assert self.dyn_levels

        il = self._get_level(level)
        var = self._get_var(varname, data.dtype, data.shape, attrs)
        var[it,il] = data
        self.filled[il][it,self.idx_var[varname]] = 1

    def add_full(self, varname, it, data, attrs={}):
        assert not self.dyn_levels

        var = self._get_var(varname, data.dtype, data.shape, attrs)
        var[it] = data
        self.filled[:,it,self.idx_var[varname]] = 1

    def _pprint_missing(self, data, axis, axname, keys=None):
        n = data.shape[axis]
        axes = list(range(len(data.shape)))
        del axes[axis]
        count = data.size // n
        nfilled = data.sum(axis=axes)
        pkeys = range(n) if keys is None else keys

        return 'Per-{}:\n{}'.format(
                axname,
                '\n'.join(
                    '{}: {}/{} ({}%)'.format(
                        k, nfilled[i], count, nfilled*100//count)
                    for i, k in enumerate(pkeys)))

    def finalize(self):
        if self.dyn_levels:
            self.levels = np.array(self.levels)
            self.filled = np.array(self.filled)
            self.fout.createVariable(self.level_dimname, self.levels.dtype,
                                     (self.level_dimname,))[:] = self.levels
            from ..logging import verbose
            verbose('Loaded levels: {}', self.levels)

        if not self.filled.all():
            from ..logging import die
            pp = [self._pprint_missing(self.filled, 2, 'variable', self.varnames),
                  self._pprint_missing(self.filled, 1, 'time')]
            if self.dyn_levels:
                pp = [self._pprint_missing(self.filled, 2, 'variable', self.varnames),
                      self._pprint_missing(self.filled, 1, 'time'),
                      self._pprint_missing(self.filled, 0, 'level', self.levels)]
            else:
                pp = [self._pprint_missing(self.filled, 1, 'variable', self.varnames),
                      self._pprint_missing(self.filled, 0, 'time')]
            die('Some input data is missing:\n\n{}', '\n\n'.join(pp))
