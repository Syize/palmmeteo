"""
config.py - Compatibility module for palmmeteo

This module provides compatibility with existing code that still imports from
palmmeteo.config instead of palmmeteo.core.config.
"""

from .core.config import (
    cfg,
    load_config,
    parse_duration,
    ConfigObj,
    duration_units
)

from .exceptions import ConfigurationError as ConfigError

__all__ = [
    "cfg",
    "load_config",
    "parse_duration",
    "ConfigObj",
    "duration_units",
    "ConfigError"
]
