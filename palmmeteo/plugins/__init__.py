"""
plugins/__init__.py - Plugin management system for PALM-meteo

This module contains the plugin management system for PALM-meteo, which has
been migrated to use pluggy for better extensibility and maintainability.

Pluggy is a Python plugin management library that provides a simple and
powerful API for creating and using plugins.
"""

from .plugin_impl import (
    Plugin,
    ImportPluginMixin,
    HInterpPluginMixin,
    VInterpPluginMixin,
    SetupPluginMixin,
    WritePluginMixin,
    plugin_factory
)

from .plugin_impl import hookimpl

from .hookspecs import (
    check_config,
    import_data,
    interpolate_horiz,
    interpolate_vert,
    setup_model,
    write_data
)

from .plugin_manager import (
    pm,
    initialize_plugins,
    execute_event,
    event_hooks
)

# Backward compatibility - aliases for existing code that might use these
plugins = []

# The plugin system is now managed by pluggy
__all__ = [
    "Plugin",
    "ImportPluginMixin",
    "HInterpPluginMixin",
    "VInterpPluginMixin",
    "SetupPluginMixin",
    "WritePluginMixin",
    "plugin_factory",
    "hookimpl",
    "check_config",
    "import_data",
    "interpolate_horiz",
    "interpolate_vert",
    "setup_model",
    "write_data",
    "pm",
    "initialize_plugins",
    "execute_event",
    "event_hooks"
]
