"""
chunking.py - Array chunking and distribution

This module contains functions for distributing arrays and tasks among
threads or processes in a balanced manner.
"""

import numpy as np
from typing import Any, Tuple, Generator

def distribute(what: int, into: int, reverse: bool = False) -> Tuple[int, ...]:
    """
    Distributes integer into integers as evenly as possible.
    
    Parameters
    ----------
    what : int
        Number to distribute
    into : int
        Number of parts to distribute into
    reverse : bool, optional
        Whether to reverse the distribution (smaller parts first), by default False
    
    Returns
    -------
    Tuple[int, ...]
        Tuple of integers representing the distribution
    """
    d, m = divmod(what, into)
    if reverse:
        return (d,)*(into-m) + (d+1,)*m
    else:
        return (d+1,)*m + (d,)*(into-m)

def distribute_chunks(sizes: Tuple[int, ...], nthreads: int, 
                     prefix: Tuple[Any, ...] = (), 
                     reverse: bool = False) -> Generator[Any, None, None]:
    """
    Distributes an n-dim array among threads as evenly as possible.
    
    Parameters
    ----------
    sizes : Tuple[int, ...]
        Dimensions of the array to distribute
    nthreads : int
        Number of threads to distribute across
    prefix : Tuple[Any, ...], optional
        Prefix for the distribution, by default ()
    reverse : bool, optional
        Whether to reverse the distribution, by default False
    
    Returns
    -------
    generator
        Generator yielding tuples representing the chunk distribution
    """

    if len(sizes) == 0:
        # Nothing more to distribute, may yield less threads
        yield prefix
    elif sizes[0] >= nthreads:
        # Final step, threads cover remaining dimension(s)
        rem = tuple(slice(0, l) for l in sizes[1:])
        start = 0
        for n in distribute(sizes[0], nthreads, not reverse):
            stop = start + n
            yield prefix + (slice(start, stop),) + rem
            start = stop
    else:
        # distribute threads into this dim's elements
        start = 0
        for n in distribute(nthreads, sizes[0], reverse):
            stop = start + 1
            # By flipping reverse back and forth we avoid systematic
            # overburdening of first/last threads
            yield from distribute_chunks(sizes[1:], n,
                    prefix + (slice(start, stop),),
                    not reverse)
            start = stop
