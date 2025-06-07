#!/usr/bin/env python3
"""
Fix common XML formatting issues in GraphML files.

This utility script repairs issues like unescaped special characters
in GraphML files to prevent parsing errors.
"""

import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union, Dict, Any, List, Tuple

# Import our XML utilities - Using relative import for module within the same package
from .xml_utils import fix_xml_file

def repair_graphml_structure(graphml_content: str) -> str:
    """
    Repair structural issues in GraphML content.
    
    Args:
        graphml_content: GraphML XML content as string
        
    Returns:
        str: Repaired GraphML XML content
    """
    content = graphml_content
    
    # Ensure root graphml element has proper namespaces
    if '<graphml' in content and 'xmlns=' not in content:
        content = re.sub(
            r'<graphml',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
            'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"',
            content
        )
    
    # Ensure graph element has edgedefault attribute
    if '<graph' in content and 'edgedefault=' not in content:
        content = re.sub(
            r'<graph\s+id="([^"]*)"',
            '<graph id="\\1" edgedefault="directed"',
            content
        )
    
    return content


def ensure_proper_keys(graphml_content: str) -> str:
    """
    Ensure GraphML has proper key definitions.
    
    Args:
        graphml_content: GraphML XML content as string
        
    Returns:
        str: GraphML XML content with proper key definitions
    """
    content = graphml_content
    
    # Check if key definitions are present
    if '<key ' not in content:
        # Extract the opening graphml tag
        match = re.search(r'<graphml[^>]*>', content)
        if match:
            opening_tag = match.group(0)
            
            # Create standard key definitions for node and edge properties
            key_defs = """
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="type" attr.type="string"/>
  <key id="d2" for="node" attr.name="desc" attr.type="string"/>
  <key id="d3" for="node" attr.name="team" attr.type="string"/>
  <key id="d4" for="node" attr.name="resp" attr.type="string"/>
  <key id="d5" for="node" attr.name="crit" attr.type="string"/>
  <key id="e0" for="edge" attr.name="label" attr.type="string"/>
  <key id="e1" for="edge" attr.name="cond" attr.type="string"/>
"""
            # Insert the key definitions after the opening tag
            content = content.replace(opening_tag, opening_tag + key_defs)
    
    return content


def fix_node_ids(graphml_content: str) -> str:
    """
    Fix invalid node IDs in GraphML content.
    
    Args:
        graphml_content: GraphML XML content as string
        
    Returns:
        str: GraphML XML content with fixed node IDs
    """
    content = graphml_content
    
    # Find all node IDs
    node_id_pattern = r'<node\s+id="([^"]*)"'
    node_ids = re.findall(node_id_pattern, content)
    
    # Track replacements to ensure consistent fixes for edges
    id_replacements = {}
    
    # Fix invalid IDs (must start with letter or underscore)
    for node_id in node_ids:
        if node_id and node_id[0].isdigit():
            new_id = f"n_{node_id}"
            id_replacements[node_id] = new_id
            
            # Replace node ID
            content = re.sub(
                f'<node\\s+id="{re.escape(node_id)}"',
                f'<node id="{new_id}"',
                content
            )
    
    # Fix corresponding edge references
    for old_id, new_id in id_replacements.items():
        # Fix source attributes
        content = re.sub(
            f'source="{re.escape(old_id)}"',
            f'source="{new_id}"',
            content
        )
        
        # Fix target attributes
        content = re.sub(
            f'target="{re.escape(old_id)}"',
            f'target="{new_id}"',
            content
        )
    
    return content


def fix_graphml_file_structure(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Fix structural issues in a GraphML file.
    
    Args:
        input_path: Path to the input GraphML file
        output_path: Path for the fixed GraphML file (optional)
        
    Returns:
        Path: Path to the fixed GraphML file
    """
    # First fix general XML issues
    fixed_xml_path = fix_xml_file(input_path, output_path)
    
    # Now fix GraphML specific structural issues
    with open(fixed_xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply GraphML-specific fixes
    content = repair_graphml_structure(content)
    content = ensure_proper_keys(content)
    content = fix_node_ids(content)
    
    # Write fixed content back to file
    with open(fixed_xml_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return fixed_xml_path


def verify_graphml_file(graphml_file: Path) -> Dict[str, Any]:
    """
    Verify a GraphML file and return diagnostic information.
    
    Args:
        graphml_file: Path to the GraphML file
        
    Returns:
        Dict[str, Any]: Diagnostic information about the file
    """
    diagnostics = {
        "file": str(graphml_file),
        "exists": graphml_file.exists(),
        "size": graphml_file.stat().st_size if graphml_file.exists() else 0,
        "can_parse": False,
        "parse_errors": None,
        "node_count": 0,
        "edge_count": 0,
        "problematic_content": []
    }
    
    if not graphml_file.exists():
        diagnostics["parse_errors"] = "File does not exist"
        return diagnostics
    
    # Check for problematic content patterns
    with open(graphml_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        
        # Check for unescaped special characters
        unescaped_ampersands = re.findall(r'&(?!amp;|lt;|gt;|quot;|apos;)[a-zA-Z0-9]', content)
        if unescaped_ampersands:
            diagnostics["problematic_content"].append(
                f"Found {len(unescaped_ampersands)} unescaped ampersands"
            )
        
        # Check for mismatched tags
        if content.count('<') != content.count('>'):
            diagnostics["problematic_content"].append("Mismatched angle brackets")
    
    try:
        # Try to parse
        tree = ET.parse(graphml_file)
        root = tree.getroot()
        diagnostics["can_parse"] = True
        
        # Count nodes and edges
        namespaces = {"": "http://graphml.graphdrawing.org/xmlns"}
        try:
            # Try with namespace
            nodes = root.findall(".//node", namespaces)
            edges = root.findall(".//edge", namespaces)
        except Exception:
            # Try without namespace
            nodes = root.findall(".//node")
            edges = root.findall(".//edge")
        
        diagnostics["node_count"] = len(nodes)
        diagnostics["edge_count"] = len(edges)
        
    except ET.ParseError as e:
        diagnostics["parse_errors"] = str(e)
    except Exception as e:
        diagnostics["parse_errors"] = f"Unexpected error: {str(e)}"
    
    return diagnostics


def main() -> int:
    """
    Main function to fix GraphML files.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix common XML formatting issues in GraphML files")
    parser.add_argument("input", help="Input GraphML file to fix")
    parser.add_argument("-o", "--output", help="Output fixed GraphML file (defaults to creating backup and overwriting input)")
    parser.add_argument("-b", "--no-backup", action="store_true", help="Don't create a backup of the original file")
    parser.add_argument("-v", "--verify", action="store_true", help="Verify file structure without fixing")
    
    args = parser.parse_args()
    
    try:
        input_path = Path(args.input)
        
        if args.verify:
            # Just verify the file structure
            diagnostics = verify_graphml_file(input_path)
            print("GraphML File Diagnostics:")
            for key, value in diagnostics.items():
                if key != "problematic_content":
                    print(f"  {key}: {value}")
                else:
                    print("  problematic_content:")
                    for issue in value:
                        print(f"    - {issue}")
            return 0
        
        output_path = Path(args.output) if args.output else None
        
        # If --no-backup is specified and no output is provided, create a new file
        if args.no_backup and output_path is None:
            output_path = input_path.with_name(f"{input_path.stem}_fixed{input_path.suffix}")
            
        fixed_path = fix_graphml_file_structure(input_path, output_path)
        print(f"Fixed GraphML file saved to: {fixed_path}")
        
        if fixed_path != input_path:
            print(f"Original file preserved at: {input_path}")
        else:
            print(f"Backup of original file created at: {input_path.with_suffix(f'{input_path.suffix}.bak')}")
        
        # Verify the fixed file
        diagnostics = verify_graphml_file(fixed_path)
        if diagnostics["can_parse"]:
            print(f"Verified: File contains {diagnostics['node_count']} nodes and {diagnostics['edge_count']} edges")
        else:
            print(f"Warning: Fixed file still has parsing issues: {diagnostics['parse_errors']}")
            
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())