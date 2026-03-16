"""
config_model.py - Pydantic models for configuration management

This module contains Pydantic models for configuration management.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, RootModel

class BaseConfig(BaseModel):
    """
    Base configuration model for all PALM-meteo specific configurations.
    """
    class Config:
        """
        Configuration for Pydantic models.
        """
        extra = 'allow'
        validate_by_name = True
        validate_assignment = True

class ConfigSection(BaseConfig):
    """
    Configuration section model for nested configuration structures.
    """
    pass

class ConfigObj(RootModel[Dict[str, Any]]):
    """
    Configuration object model, representing a hierarchical configuration.
    """
    # We use dynamic fields to allow for any configuration structure

    def __getattr__(self, name: str) -> Any:
        try:
            value = self.root[name]
            # If the value is a dict, wrap it in a ConfigObj for nested access
            if isinstance(value, dict):
                return ConfigObj(value)
            # If the value is a list, wrap each dict element in a ConfigObj
            if isinstance(value, list):
                return [ConfigObj(item) if isinstance(item, dict) else item for item in value]
            return value
        except KeyError:
            raise AttributeError(f'Attribute {name} not found')

    def __getitem__(self, key: str) -> Any:
        try:
            value = self.root[key]
            if isinstance(value, dict):
                return ConfigObj(value)
            if isinstance(value, list):
                return [ConfigObj(item) if isinstance(item, dict) else item for item in value]
            return value
        except KeyError:
            raise KeyError(f'Key {key} not found')

    def __contains__(self, key: str) -> bool:
        return key in self.root

    def __iter__(self):
        return iter(self.root.items())

    def __setattr__(self, name: str, value: Any):
        # Allow setting fields through dot notation
        if name in ['root', '__fields_set__', '__config__', '__class__']:
            super().__setattr__(name, value)
        else:
            if isinstance(value, ConfigObj):
                self.root[name] = value.root
            elif isinstance(value, dict):
                self.root[name] = value
            elif isinstance(value, list):
                self.root[name] = [item.root if isinstance(item, ConfigObj) else item for item in value]
            else:
                self.root[name] = value

    def __setitem__(self, key: str, value: Any):
        # Allow setting fields through key-value notation
        if isinstance(value, ConfigObj):
            self.root[key] = value.root
        elif isinstance(value, dict):
            self.root[key] = value
        elif isinstance(value, list):
            self.root[key] = [item.root if isinstance(item, ConfigObj) else item for item in value]
        else:
            self.root[key] = value

    def _get_path(self) -> List[str]:
        """
        Get the path of this configuration section relative to the root.

        Returns
        -------
        List[str]
            Path of this configuration section
        """
        # Note: This implementation assumes that the ConfigObj hierarchy is
        #       not too deep and that each node has a parent. For the purposes
        #       of error reporting, this should suffice.
        return []

    def _ingest_module_config(self, modname: str) -> None:
        """
        Locates the initial configuration file config_init.yaml within module
        code and ingests it.
        """
        import importlib.resources
        from ..logging import die, verbose

        fpath = importlib.resources.files(modname).joinpath('config_init.yaml')

        if not fpath.is_file():
            die('Cannot find initial configuration for package {}! Expected at {}.',
                modname, fpath)

        verbose('Loading {} configuration from {}', modname, fpath)
        with fpath.open('r') as f:
            from yaml import load
            try:
                from yaml import CSafeLoader as SafeLoader
            except ImportError:
                from yaml import SafeLoader
            self._ingest_dict(load(f, Loader=SafeLoader))

    def _ingest_dict(self, d: Dict[str, Any], overwrite: bool = True, 
                   extend: bool = False, check_exist: bool = False) -> None:
        """
        Ingest a dictionary into the configuration object.

        Parameters
        ----------
        d : dict
            Dictionary to ingest
        overwrite : bool, optional
            Whether to overwrite existing values, by default True
        extend : bool, optional
            Whether to extend lists instead of replacing them, by default False
        check_exist : bool, optional
            Whether to check if settings exist before overwriting, by default False
        """
        for k, v in d.items():
            if isinstance(v, dict):
                # For a dictionary (top-level or with only dictionaries above,
                # i.e. a subsection), we recurse
                do_check_exist = check_exist
                try:
                    vl = self[k]
                except KeyError:
                    # not yet present: create a new empty child node
                    vl = ConfigObj({})
                    self[k] = vl
                    if self.root.get('__user_expandable__', False):
                        do_check_exist = False
                try:
                    vl._ingest_dict(v, overwrite, extend, do_check_exist)
                except AttributeError:
                    raise TypeError('Trying to replace a non-dictionary setting with a dictionary')
            elif extend and isinstance(v, list):
                # We extend lists if requested
                vl = self.root.setdefault(k, [])
                try:
                    vl.extend(v)
                except AttributeError:
                    raise TypeError('Trying to extend a non-list setting with a list')
            elif v is None and isinstance(self.root.get(k), dict):
                # This is a special case: we are replacing an existing section
                # with None. That most probably means that the user has
                # presented an empty section (possibly with all values
                # commented out). In that case, we do not want to erase that
                # section. To actually erase a whole section, the user can
                # still present empty dictionary using the following syntax:
                # section_name: {}
                pass
            else:
                # Non-extended lists and all other objects are considered as
                # values and they are copied as-is (including their subtrees if
                # present). Non-null values are overwritten only if
                # overwrite=True.
                if overwrite:
                    if check_exist and k not in self.root:
                        from ..logging import warn
                        warn('WARNING: ignoring an unknown setting {}={}.', k, v)
                    self.root[k] = v
                else:
                    if self.root.get(k, None) is None:
                        self.root[k] = v