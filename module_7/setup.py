"""
setup.py

Packaging metadata for module_5.

This file makes the project installable (including editable installs) so imports
and tooling behave consistently across local runs and CI.
"""

from setuptools import find_packages, setup


setup(
    name="module_5",
    version="0.1.0",
    description="JHU Modern Software Concepts - Module 5",
    packages=find_packages(),
    python_requires=">=3.11",
)