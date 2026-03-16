"""
sliceutils.py - Slice manipulation utilities

This module contains classes and functions for extending and manipulating slices.
"""

from typing import Union, Tuple, Any

class SliceExtender:
    __slots__ = ['slice_obj', 'slices']

    def __init__(self, slice_obj: Any, *slices: Any):
        """
        Initialize a SliceExtender instance.
        
        Parameters
        ----------
        slice_obj : Any
            Object that supports slicing
        *slices : Any
            Slices to extend
        """
        self.slice_obj = slice_obj
        self.slices = slices

    def __getitem__(self, key: Union[slice, Tuple[slice, ...]]) -> Any:
        """
        Apply extended slicing.
        
        Parameters
        ----------
        key : Union[slice, Tuple[slice, ...]]
            Slice or tuple of slices to apply
        
        Returns
        -------
        Any
            Result of the extended slicing
        """
        if isinstance(key, tuple):
            return self.slice_obj[key+self.slices]
        else:
            return self.slice_obj[(key,)+self.slices]

class SliceBoolExtender:
    __slots__ = ['slice_obj', 'slices', 'boolindex']

    def __init__(self, slice_obj: Any, slices: Tuple[Any, ...], boolindex: Any):
        """
        Initialize a SliceBoolExtender instance.
        
        Parameters
        ----------
        slice_obj : Any
            Object that supports slicing
        slices : Tuple[Any, ...]
            Slices to extend
        boolindex : Any
            Boolean index to apply
        """
        self.slice_obj = slice_obj
        self.slices = slices
        self.boolindex = boolindex

    def __getitem__(self, key: Union[slice, Tuple[slice, ...]]) -> Any:
        """
        Apply extended slicing with boolean index.
        
        Parameters
        ----------
        key : Union[slice, Tuple[slice, ...]]
            Slice or tuple of slices to apply
        
        Returns
        -------
        Any
            Result of the extended slicing with boolean index applied
        """
        if isinstance(key, tuple):
            v = self.slice_obj[key+self.slices]
        else:
            v = self.slice_obj[(key,)+self.slices]
        return v[...,self.boolindex]
