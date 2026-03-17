"""
runtime.py - Compatibility module for palmmeteo

This module provides compatibility with existing code that still imports from
palmmeteo.runtime instead of palmmeteo.core.runtime.
"""

from .core.runtime import (
    rt,
    RuntimeObj,
    myopen
)

__all__ = [
    "rt",
    "RuntimeObj",
    "myopen"
]
