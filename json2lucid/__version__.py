"""
Version information for JSON2Lucid.

This module contains version information for the JSON2Lucid package.
It follows Semantic Versioning 2.0.0 (https://semver.org/).
"""

from typing import Tuple, Union

__version__ = "1.0.0"
__version_info__: Tuple[Union[int, str], ...] = tuple(
    int(x) if x.isdigit() else x
    for x in __version__.replace("-", ".", 1).split(".")
)

def get_version() -> str:
    """
    Get the current version string.
    
    Returns:
        str: The current version string
    """
    return __version__

def get_version_info() -> Tuple[Union[int, str], ...]:
    """
    Get the version info as a tuple.
    
    Returns:
        Tuple[Union[int, str], ...]: Version info (major, minor, patch[, label])
    """
    return __version_info__