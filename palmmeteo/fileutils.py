"""
fileutils.py - File and directory operations

This module contains utility functions for working with files and directories.
"""

import os
import re
from typing import Optional

fext_re = re.compile(r'\.(\d{3})$')

def find_free_fname(fpath: str, overwrite: bool = False) -> str:
    """
    Find a free filename by appending a numeric suffix if the file already exists.
    
    Parameters
    ----------
    fpath : str
        Original file path
    overwrite : bool, optional
        If True, will return the original path even if it exists, by default False
    
    Returns
    -------
    str
        Free filename (may be the original path or a modified version with a suffix)
    
    Raises
    ------
    RuntimeError
        If no free filename can be found (maximum suffix of 999 reached)
    """
    if not os.path.exists(fpath):
        return fpath

    if overwrite:
        from .logging import log
        log('Existing file {} will be overwritten.', fpath)
        return fpath

    # Try to find free fpath.###
    path, base = os.path.split(fpath)
    nbase = len(base)
    maxnum = -1
    for fn in os.listdir(path):
        if not fn.startswith(base):
            continue
        m = fext_re.match(fn[nbase:])
        if not m:
            continue
        maxnum = max(maxnum, int(m.group(1)))
    if maxnum >= 999:
        raise RuntimeError('Cannot find free filename starting with ' + fpath)

    newpath = '{}.{:03d}'.format(fpath, maxnum+1)
    from .logging import log
    log('Filename {} exists, using {}.', fpath, newpath)
    return newpath

def assert_dir(filepath: str) -> None:
    """
    Creates a directory for an output file if it doesn't exist already.
    
    Parameters
    ----------
    filepath : str
        Path to the file for which to ensure the directory exists
    """
    dn = os.path.dirname(filepath)
    if not os.path.isdir(dn):
        os.makedirs(dn)
