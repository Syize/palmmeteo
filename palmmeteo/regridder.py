"""
regridder.py - Grid regridding and coordinate transformation

This module contains classes and functions for regridding data from one grid
to another using Delaunay triangulation and barycentric coordinate
interpolation.
"""

import numpy as np
from scipy.spatial import Delaunay

from .constants import ax_, rad
from .physics import PalmPhysics
from .logging import die, warn, log, verbose
from .sliceutils import SliceBoolExtender
from .exceptions import InterpolationError

def barycentric(tri, pt, isimp):
    """Calculate barycentric coordinates of a multi-dimensional point set
    within a triangulation.

    :param pt:      selection of points (multi-dimensional)
    :param isimp:   selection of simplices (same dims as pt)
    """
    sel_transform = tri.transform[isimp,:,:] #transform(simp, bary, cart) -> (pt, bary, cart)

    # based on help(Delaunay), changing np.dot to selection among dims, using
    # selected simplices
    fact2 = (pt - sel_transform[...,2,:])[...,ax_,:]
    bary0 = (sel_transform[...,:2,:] * fact2).sum(axis=-1) #(pt, bary[:2])

    # add third barycentric coordinate
    bary = np.concatenate((bary0, (1.-bary0.sum(axis=-1))[...,ax_]), axis=-1)
    return bary

class TriRegridder:
    """Universal regridder which uses Delaunay triangulation and barycentric
    coordinate interpolation.

    Works on any grid - triangular, rectangular or unstructured. The only
    requirements are the arrays of latitude and longitude coordinates. The grid
    arrays may be organized as 1- or 2-dimensional.
    """
    def __init__(self, clat, clon, ylat, xlon, buffer):
        #ylat = ylat[0,:5]
        #xlon = xlon[0,:5]
        # Simple Mercator-like stretching for equidistant lat/lon coords
        self.lon_coef = np.cos(ylat.mean()*rad)

        deg_range = buffer / (PalmPhysics.radius*rad)
        lat0 = ylat.min() - deg_range
        lat1 = ylat.max() + deg_range
        deg_range /= self.lon_coef
        lon0 = xlon.min() - deg_range
        lon1 = xlon.max() + deg_range
        verbose(f'Using range lat = {lat0} .. {lat1}, lon = {lon0} .. {lon1}.')

        verbose('Selecting points for triangulation.')
        ptmask_full = (lat0 <= clat) & (clat <= lat1) & (lon0 <= clon) & (clon <= lon1)
        self.ndim = len(ptmask_full.shape)
        self.npt = ptmask_full.sum()
        if not self.npt:
            raise InterpolationError('No points for target area found in the input data!')

        # Multidimensional coordinates. Needs per-dimension slices for
        # efficient loading from NetCDF.
        counts = []
        slices = []
        for iax, nax in enumerate(ptmask_full.shape):
            ax_nonzero = ptmask_full.sum(axis=tuple(n for n in range(self.ndim) if n != iax),
                    dtype=bool)
            ax0 = ax_nonzero.argmax()
            ax1 = nax - ax_nonzero[::-1].argmax()
            slices.append(slice(ax0, ax1))
            counts.append((ax1-ax0, nax))
        self.slices = tuple(slices)
        self.ptmask = ptmask_full[self.slices]
        verbose(f'Selected {self.npt} points out of {clat.size} total in {self.ndim} dimensions.')
        verbose('Pre-selection using per-dimension slices: {} from {} ({}).',
                self.ptmask.size, clat.size,
                ', '.join(f'{ns} from {nt}' for ns, nt in counts))

        verbose('Triangulating.')
        sclat = clat[ptmask_full]
        sclon = clon[ptmask_full]
        sclonx = sclon * self.lon_coef
        tri = Delaunay(np.transpose([sclat, sclonx]))

        # identify simplices
        xlonx = xlon * self.lon_coef
        pt = np.concatenate((ylat[:,:,ax_], xlonx[:,:,ax_]), axis=2)
        isimp = tri.find_simplex(pt)
        assert (isimp >= 0).all()

        self.bary = barycentric(tri, pt, isimp)

        self.simp = tri.simplices[isimp] #(pt,bary)

    def loader(self, obj):
        """Prepares a slicing object which automatically adds selector indices
        for this regridder.
        """
        return SliceBoolExtender(obj, self.slices, self.ptmask)

    def regrid(self, data):
        """Regrid from point set selected using loader"""

        sel_data = data[...,self.simp] #(pt,bary)
        return (sel_data * self.bary).sum(axis=-1)

def verify_palm_hinterp(regridder, lats, lons):
    """Regrids source lat+lon coordinates to PALM coordinates using the regridder and verifies the result."""
    from .runtime import rt

    diff = regridder.regrid(lats) - rt.palm_grid_lat
    log('Regridder verification for latitudes:  Error [deg]: {:9.3g} .. {:9.3g} '
        '(bias={:9.3g}, MAE={:8.3g}, RMSE={:8.3g}).',
        diff.min(), diff.max(), diff.mean(), np.abs(diff).mean(),
        np.sqrt(np.square(diff).mean()))

    diff = regridder.regrid(lons) - rt.palm_grid_lon
    log('Regridder verification for longitudes: Error [deg]: {:9.3g} .. {:9.3g} '
        '(bias={:9.3g}, MAE={:8.3g}, RMSE={:8.3g}).',
        diff.min(), diff.max(), diff.mean(), np.abs(diff).mean(),
        np.sqrt(np.square(diff).mean()))

    verbose('NOTE: 1 metre =~ 0.9e-5 degrees of latitudes.')

def parse_linspace(space, name, maxerr):
    """Verifies that a vector is evenly-spaced and returns the parameters
    of such spacing.
    """
    n = len(space)
    base = space[0]
    step = (space[-1] - base) / (n-1)
    dstep = 1. / step
    max_error = np.abs((space - base) * dstep  -
                       np.arange(n, dtype=space.dtype)).max()

    if max_error > maxerr:
        die('Error: Maximum error in {} = {} times grid '
                'spacing!', name, max_error)
    else:
        verbose('Maximum error in {} = {} times grid '
                'spacing - OK.', name, max_error)

    return base, step, dstep

class LatLonRegularGrid:
    """Coordinate transformer for simple regular lat-lon grids"""

    def __init__(self, lats, lons):
        lat_base, lat_step, lat_dstep = parse_linspace(lats,
                'input grid latitudes', __import__('palmmeteo.config').cfg.hinterp.max_input_grid_error)
        lon_base, lon_step, lon_dstep = parse_linspace(lons,
                'input grid longitudes', __import__('palmmeteo.config').cfg.hinterp.max_input_grid_error)

        self.latlon_to_ji = lambda lat, lon: ((lat-lat_base)*lat_dstep, (lon-lon_base)*lon_dstep)
        self.ji_to_latlon = lambda j, i: (j*lat_step+lat_base, i*lon_step+lon_base)
