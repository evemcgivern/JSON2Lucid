#!/usr/bin/env python3
"""
Setup script for JSON2Lucid package.

This script configures the package for installation using pip.
It includes all dependencies, entry points, and metadata.
"""

import os
from setuptools import setup, find_packages
from pathlib import Path
import re
from json2lucid.__version__ import __version__ as VERSION

# Read the long description from README if it exists
README = (Path(__file__).parent / "README.md").read_text(encoding='utf-8') if (Path(__file__).parent / "README.md").exists() else ""

# Define package requirements
INSTALL_REQUIRES = [
    "lxml>=4.9.3",         # Enhanced XML processing capabilities
    "numpy>=1.24.0",       # Required for any numerical operations
    "pillow>=10.0.0",      # Image processing for PlantUML diagram generation
    "requests>=2.31.0",    # For any HTTP requests
    "typing-extensions>=4.7.1",  # Extended typing capabilities for Python <3.11
]

# Development dependencies for contributors
DEV_REQUIRES = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.7.0",
    "flake8>=6.1.0",
    "isort>=5.12.0",
    "mypy>=1.4.1",
    "pylint>=2.17.5",
    "pyinstaller>=5.13.0",  # Add this line
]

setup(
    name="json2lucid",
    version=VERSION,
    description="Convert JSON workflow definitions to various diagram formats including Lucidchart",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/eve-mcgivern/json2lucid",
    author="Eve McGivern",
    author_email="eve.mcgivern@sands.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",  # This replaces the license parameter
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    packages=find_packages(exclude=["tests", "examples"]),
    include_package_data=True,
    package_data={
        "json2lucid": ["utils/*.ico", "utils/*.png"],
    },
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": DEV_REQUIRES,
    },
    entry_points={
        "console_scripts": [
            "json2lucid=json2lucid.format_converter:main",
            "json2lucid-gui=json2lucid.converter_gui:main",
        ],
    },
    python_requires=">=3.8",
)