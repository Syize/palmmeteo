"""
core module
===========

This module contains core functionality of the PALM-meteo software.
"""

from .config import cfg, load_config
from .runtime import rt, basic_init
from .dispatch import run, main

__all__ = ['cfg', 'load_config', 'rt', 'basic_init', 'run', 'main']
