#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from palmmeteo.core.dispatch import run

def test_plugin_system():
    # Create a simple mock object for argv
    class MockArgv:
        def __init__(self):
            self.config = ['examples/test_config.yaml']  # Use test configuration
            self.workflow = ['check_config']
            self.workflow_from = None
            self.workflow_to = None
            self.verbosity_arg = None
            self.tasks = []

    # Load configuration
    run(MockArgv())

    print("Plugin system initialized successfully")

if __name__ == "__main__":
    test_plugin_system()
