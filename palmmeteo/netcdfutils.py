"""
netcdfutils.py - NetCDF file utilities

This module contains utility functions for working with NetCDF files.
"""

from .exceptions import DataError

def ensure_dimension(f: Any, dimname: str, dimsize: int) -> Any:
    """
    Creates a dimension in a netCDF file or verifies its size if it already
    exists.
    
    Parameters
    ----------
    f : netCDF4.Dataset
        NetCDF file object
    dimname : str
        Name of the dimension to create or verify
    dimsize : int or None
        Size of the dimension. If None, creates an unlimited dimension.
    
    Returns
    -------
    netCDF4.Dimension
        Dimension object
    """
    try:
        d = f.dimensions[dimname]
    except KeyError:
        # Dimension is missing - create it and return
        return f.createDimension(dimname, dimsize)

    # Dimension is present
    if dimsize is None:
        # Wanted unlimited dim, check that it is
        if not d.isunlimited():
            raise DataError('Dimension {} is already present and it is not unlimited as requested'.format(dimname), variable=dimname)
    else:
        # Fixed size dim - compare sizes
        if len(d) != dimsize:
            raise DataError('Dimension {} is already present and its size {} differs from requested {}'.format(dimname, len(d), dimsize), variable=dimname)
    return d

def getvar(f: Any, varname: str, *args: Any, **kwargs: Any) -> Any:
    """
    Creates a variable in a netCDF file or returns it if it already exists.
    Does NOT verify its parameters.
    
    Parameters
    ----------
    f : netCDF4.Dataset
        NetCDF file object
    varname : str
        Name of the variable to create or retrieve
    *args : Any
        Additional positional arguments for createVariable
    **kwargs : Any
        Additional keyword arguments for createVariable
    
    Returns
    -------
    netCDF4.Variable
        Variable object
    """
    try:
        v = f.variables[varname]
    except KeyError:
        return f.createVariable(varname, *args, **kwargs)
    return v
