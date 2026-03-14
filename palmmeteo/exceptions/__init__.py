"""
exceptions module
==================

This module contains exception classes for the PALM-meteo software.
"""

from .exceptions import (
    PalmMeteoException,
    ConfigurationError,
    CalculationError,
    ImportError,
    InterpolationError,
    PluginError,
    DataError,
    FileError,
    WorkflowError
)

__all__ = [
    'PalmMeteoException',
    'ConfigurationError',
    'CalculationError',
    'ImportError',
    'InterpolationError',
    'PluginError',
    'DataError',
    'FileError',
    'WorkflowError'
]
