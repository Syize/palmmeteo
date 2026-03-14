"""
exceptions.py - PALM-meteo exception hierarchy

This module defines a unified exception hierarchy for PALM-meteo, providing
more specific and descriptive exception classes for different types of errors.
"""

class PalmMeteoException(Exception):
    """
    Base exception class for all PALM-meteo specific exceptions.
    
    All exceptions raised by PALM-meteo should inherit from this class.
    """
    
    def __init__(self, message: str = "", *args: object) -> None:
        """
        Initialize a PalmMeteoException.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        """
        super().__init__(message, *args)
        self.message = message


class ConfigurationError(PalmMeteoException):
    """
    Exception raised for configuration-related errors.
    
    This exception is raised when there are errors in configuration files,
    settings, or parameters.
    """
    
    def __init__(self, message: str = "", section: str = None, key: str = None, value: str = None, *args: object):
        """
        Initialize a ConfigurationError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        section : str, optional
            Configuration section where the error occurred, by default None
        key : str, optional
            Configuration key where the error occurred, by default None
        value : str, optional
            Configuration value that caused the error, by default None
        """
        self.section = section
        self.key = key
        self.value = value
        
        if section and key:
            msg_parts = [message]
            msg_parts.append(f", item: {section}:{key}")
            if value is not None:
                msg_parts.append(f", value: {value}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)


class CalculationError(PalmMeteoException):
    """
    Exception raised for calculation-related errors.
    
    This exception is raised when there are errors in numerical calculations,
    formula evaluation, or data processing.
    """
    
    def __init__(self, message: str = "", formula: str = None, value: str = None, *args: object):
        """
        Initialize a CalculationError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        formula : str, optional
            Formula or expression that caused the error, by default None
        value : str, optional
            Value that caused the error, by default None
        """
        self.formula = formula
        self.value = value
        
        if formula:
            msg_parts = [message]
            msg_parts.append(f", formula: {formula}")
            if value is not None:
                msg_parts.append(f", value: {value}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)


class ImportError(PalmMeteoException):
    """
    Exception raised for data import-related errors.
    
    This exception is raised when there are errors in importing data from
    external sources or files.
    """
    
    def __init__(self, message: str = "", file_path: str = None, source: str = None, *args: object):
        """
        Initialize an ImportError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        file_path : str, optional
            Path to the file that caused the error, by default None
        source : str, optional
            Data source that caused the error, by default None
        """
        self.file_path = file_path
        self.source = source
        
        if file_path or source:
            msg_parts = [message]
            if source:
                msg_parts.append(f", source: {source}")
            if file_path:
                msg_parts.append(f", file: {file_path}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)


class InterpolationError(PalmMeteoException):
    """
    Exception raised for interpolation-related errors.
    
    This exception is raised when there are errors in horizontal or vertical
    interpolation of data.
    """
    
    def __init__(self, message: str = "", method: str = None, coordinates: str = None, *args: object):
        """
        Initialize an InterpolationError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        method : str, optional
            Interpolation method used, by default None
        coordinates : str, optional
            Coordinates where the error occurred, by default None
        """
        self.method = method
        self.coordinates = coordinates
        
        if method or coordinates:
            msg_parts = [message]
            if method:
                msg_parts.append(f", method: {method}")
            if coordinates:
                msg_parts.append(f", coordinates: {coordinates}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)


class PluginError(PalmMeteoException):
    """
    Exception raised for plugin-related errors.
    
    This exception is raised when there are errors in plugin loading,
    initialization, or execution.
    """
    
    def __init__(self, message: str = "", plugin_name: str = None, plugin_type: str = None, *args: object):
        """
        Initialize a PluginError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        plugin_name : str, optional
            Name of the plugin that caused the error, by default None
        plugin_type : str, optional
            Type of the plugin that caused the error, by default None
        """
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type
        
        if plugin_name or plugin_type:
            msg_parts = [message]
            if plugin_name:
                msg_parts.append(f", plugin: {plugin_name}")
            if plugin_type:
                msg_parts.append(f", type: {plugin_type}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)


class DataError(PalmMeteoException):
    """
    Exception raised for data-related errors.
    
    This exception is raised when there are errors in data format,
    consistency, or validity.
    """
    
    def __init__(self, message: str = "", variable: str = None, dimension: str = None, *args: object):
        """
        Initialize a DataError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        variable : str, optional
            Variable that caused the error, by default None
        dimension : str, optional
            Data dimension that caused the error, by default None
        """
        self.variable = variable
        self.dimension = dimension
        
        if variable or dimension:
            msg_parts = [message]
            if variable:
                msg_parts.append(f", variable: {variable}")
            if dimension:
                msg_parts.append(f", dimension: {dimension}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)


class FileError(PalmMeteoException):
    """
    Exception raised for file-related errors.
    
    This exception is raised when there are errors in file operations such as
    reading, writing, or finding files.
    """
    
    def __init__(self, message: str = "", file_path: str = None, operation: str = None, *args: object):
        """
        Initialize a FileError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        file_path : str, optional
            Path to the file that caused the error, by default None
        operation : str, optional
            File operation that failed, by default None
        """
        self.file_path = file_path
        self.operation = operation
        
        if file_path or operation:
            msg_parts = [message]
            if operation:
                msg_parts.append(f", operation: {operation}")
            if file_path:
                msg_parts.append(f", file: {file_path}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)


class WorkflowError(PalmMeteoException):
    """
    Exception raised for workflow-related errors.
    
    This exception is raised when there are errors in the workflow execution,
    such as stage dependencies, snapshot handling, or task management.
    """
    
    def __init__(self, message: str = "", stage: str = None, task: str = None, *args: object):
        """
        Initialize a WorkflowError.
        
        Parameters
        ----------
        message : str, optional
            Exception message, by default ""
        stage : str, optional
            Workflow stage where the error occurred, by default None
        task : str, optional
            Workflow task where the error occurred, by default None
        """
        self.stage = stage
        self.task = task
        
        if stage or task:
            msg_parts = [message]
            if stage:
                msg_parts.append(f", stage: {stage}")
            if task:
                msg_parts.append(f", task: {task}")
            message = "".join(msg_parts)
            
        super().__init__(message, *args)
