#!/usr/bin/env python3
"""
Universal format converter module for diagram formats.

This module provides a unified interface for converting between
various diagram formats (JSON, GraphML, PUML, Lucidchart).
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union, Tuple, Dict, Any, List

# Import converters
from json_to_graphml import convert_json_to_graphml
from graphml_to_lucidchart import graphml_to_lucidchart


class FormatConverter:
    """
    Unified converter for diagram formats.
    
    This class provides methods to convert between different diagram formats
    by chaining converters in the appropriate sequence.
    """
    
    # Supported input formats
    INPUT_FORMATS = {
        "json": [".json"],
        "graphml": [".graphml", ".xml"],
        "puml": [".puml", ".plantuml"]
    }
    
    # Supported output formats
    OUTPUT_FORMATS = {
        "graphml": ".graphml",
        "lucidchart_uml": ".uml",
        "lucidchart_csv": ".csv",
        "puml": ".puml"
    }
    
    @classmethod
    def detect_format(cls, file_path: Union[str, Path]) -> str:
        """
        Detect the format of a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Detected format name
            
        Raises:
            ValueError: If the format cannot be detected
        """
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        for fmt, extensions in cls.INPUT_FORMATS.items():
            if extension in extensions:
                return fmt
        
        raise ValueError(f"Unsupported file format: {extension}")
    
    @classmethod
    def convert(
        cls,
        input_path: Union[str, Path],
        output_format: str,
        output_path: Optional[Union[str, Path]] = None,
        diagram_type: str = "sequence",
        auto_fix: bool = True
    ) -> Path:
        """
        Convert a file from its format to the target format.
        
        Args:
            input_path: Path to the input file
            output_format: Target format (one of OUTPUT_FORMATS keys)
            output_path: Path for the output file (default: auto-generated)
            diagram_type: Type of diagram for Lucidchart output ('sequence' or 'flowchart')
            auto_fix: Whether to automatically fix formatting errors
            
        Returns:
            Path: Path to the created output file
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            ValueError: If the format is unsupported or conversion fails
        """
        input_path_obj = Path(input_path)
        
        if not input_path_obj.exists():
            raise FileNotFoundError(f"Input file not found: {input_path_obj}")
        
        # Detect input format
        input_format = cls.detect_format(input_path_obj)
        
        # Validate output format
        if output_format not in cls.OUTPUT_FORMATS:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Determine appropriate conversion path
        if input_format == "json":
            if output_format == "graphml":
                # Direct JSON to GraphML
                return convert_json_to_graphml(input_path_obj, output_path)
            elif output_format.startswith("lucidchart_"):
                # JSON -> GraphML -> Lucidchart
                is_csv = output_format == "lucidchart_csv"
                
                # Step 1: Convert to intermediate GraphML
                temp_graphml = input_path_obj.with_name(f"{input_path_obj.stem}_temp.graphml")
                try:
                    graphml_path = convert_json_to_graphml(input_path_obj, temp_graphml)
                    
                    # Step 2: Convert GraphML to Lucidchart format
                    result = graphml_to_lucidchart(
                        graphml_path,
                        output_path,
                        diagram_type,
                        "csv" if is_csv else "uml",
                        auto_fix
                    )
                    
                    # Clean up temporary file
                    if temp_graphml.exists():
                        temp_graphml.unlink()
                    
                    return result
                    
                except Exception as e:
                    # Clean up on error
                    if temp_graphml.exists():
                        temp_graphml.unlink()
                    raise e
                
        elif input_format == "graphml":
            if output_format.startswith("lucidchart_"):
                # Direct GraphML to Lucidchart
                is_csv = output_format == "lucidchart_csv"
                return graphml_to_lucidchart(
                    input_path_obj,
                    output_path,
                    diagram_type,
                    "csv" if is_csv else "uml",
                    auto_fix
                )
        
        # For other conversions or unsupported paths
        raise ValueError(f"Conversion from {input_format} to {output_format} is not supported")


def main() -> int:
    """
    Main function to convert between diagram formats.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    import argparse
    
    # Create argument parser
    parser = argparse.ArgumentParser(description="Convert between diagram formats")
    parser.add_argument("input", help="Input file path")
    parser.add_argument(
        "-f", "--format", 
        choices=list(FormatConverter.OUTPUT_FORMATS.keys()),
        required=True,
        help="Output format"
    )
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "-t", "--type", 
        choices=["sequence", "flowchart"], 
        default="sequence",
        help="Diagram type for Lucidchart output (default: sequence)"
    )
    parser.add_argument(
        "--no-fix",
        action="store_true",
        help="Disable automatic fixing of format errors"
    )
    
    args = parser.parse_args()
    
    try:
        # Convert using the unified converter
        output_path = FormatConverter.convert(
            args.input,
            args.format,
            args.output,
            args.type,
            not args.no_fix
        )
        
        print(f"Successfully converted to {args.format}: {output_path}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())