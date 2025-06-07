#!/usr/bin/env python3
"""
Build script for creating Windows executable of JSON2Lucid.

This script uses PyInstaller to create a standalone executable
for the GUI version of the application.
"""

import os
import sys
import warnings
from pathlib import Path
import PyInstaller.__main__

def suppress_setuptools_warning() -> None:
    """Suppress the pkg_resources deprecation warning."""
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        message="pkg_resources is deprecated as an API"
    )

def get_package_path() -> Path:
    """
    Get the path to the json2lucid package directory.
    
    Returns:
        Path: Path to the package directory
    """
    project_root = Path(__file__).parent
    package_dir = project_root / "json2lucid"
    
    if not package_dir.exists():
        raise FileNotFoundError(
            f"Package directory not found at {package_dir}. "
            "Ensure the json2lucid package is properly installed."
        )
    
    return package_dir

def build_executable() -> None:
    """
    Build GUI executable for JSON2Lucid.
    """
    # Suppress deprecation warning
    suppress_setuptools_warning()
    
    # Get package directory
    package_dir = get_package_path()
    
    # Verify source files exist
    gui_path = package_dir / "converter_gui.py"
    icon_path = package_dir / "utils" / "icon.ico"
    
    if not gui_path.exists():
        raise FileNotFoundError(f"GUI script not found at {gui_path}")
    if not icon_path.exists():
        print(f"Warning: Icon file not found at {icon_path}")
    
    # PyInstaller options
    options = [
        '--clean',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--paths', str(package_dir),
        '--add-data', f'{str(package_dir / "utils")}/*{os.pathsep}utils',
        '--name', 'json2lucid'
    ]
    
    # Add icon if available
    if icon_path.exists():
        options.extend([
            '--add-data', f'{str(icon_path)}{os.pathsep}utils',
            '--icon', str(icon_path)
        ])

    try:
        # Build GUI version
        print("Building JSON2Lucid executable...")
        PyInstaller.__main__.run([
            *options,
            str(gui_path),
        ])

        print("\nBuild complete! Executable can be found at:")
        print("  - dist/json2lucid.exe")

    except Exception as e:
        print(f"Error during build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()