"""
Command Line Interface (CLI) Framework
======================================

A reusable, modular terminal framework. Provides command parsing, history,
help generation, and a clean registration API for adding custom commands.
"""

from .framework import CLI, Colors

__all__ = ["CLI", "Colors"]
