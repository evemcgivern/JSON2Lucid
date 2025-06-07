#!/usr/bin/env python3
"""
Convert GraphML files to Lucidchart-compatible formats.

This script transforms GraphML files into simplified UML notation or CSV format
that can be directly imported into Lucidchart for sequence diagrams or flowcharts.
"""

import os
import sys
import xml.etree.ElementTree as ET
import re
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Set, Any

# Import utilities from existing modules
from graphml_to_plantuml import extract_graphml_data


def create_lucidchart_sequence_diagram(nodes: List[Dict], edges: List[Dict]) -> str:
    """
    Create Lucidchart-compatible sequence diagram markup from nodes and edges.
    
    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
    
    Returns:
        str: String containing Lucidchart-compatible UML markup
    """
    # Create a mapping of node IDs to readable names
    node_names = {}
    for node in nodes:
        node_id = node["id"]
        node_name = node.get("name", node_id)
        # Clean the name to ensure it works in Lucidchart
        clean_name = re.sub(r'[^\w\s]', '_', node_name)
        node_names[node_id] = clean_name
    
    # Build sequence diagram lines
    uml_lines = []
    
    # Add header comment
    uml_lines.append("# Lucidchart Sequence Diagram")
    uml_lines.append("# Generated from GraphML file")
    uml_lines.append("")
    
    # Process edges to create interaction lines
    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]
        
        # Skip if source or target not in our nodes
        if source_id not in node_names or target_id not in node_names:
            continue
        
        source_name = node_names[source_id]
        target_name = node_names[target_id]
        
        # Get message label if any
        label = ""
        if "label" in edge:
            label = edge["label"]
        else:
            for prop_key in ["cond", "label", "condition"]:
                if prop_key in edge.get("properties", {}):
                    label = edge["properties"][prop_key]
                    break
        
        # Create the interaction line
        if label:
            uml_lines.append(f"{source_name} -> {target_name}: {label}")
        else:
            uml_lines.append(f"{source_name} -> {target_name}")
    
    # Add notes for node details (one note per node with relevant properties)
    for node in nodes:
        node_id = node["id"]
        if node_id not in node_names:
            continue
            
        node_name = node_names[node_id]
        properties = node.get("properties", {})
        
        # Collect relevant properties
        note_content = []
        
        # Check for team information
        if "team" in properties and properties["team"]:
            note_content.append(f"Team: {properties['team']}")
        
        # Check for responsibilities
        if "resp" in properties and properties["resp"]:
            note_content.append(f"Responsibilities: {properties['resp']}")
        
        # Check for entry condition
        if "cond" in properties and properties["cond"]:
            note_content.append(f"Condition: {properties['cond']}")
        
        # Add the note if we have content
        if note_content:
            note_text = ", ".join(note_content)
            uml_lines.append(f"note right of {node_name}: {note_text}")
    
    return "\n".join(uml_lines)


def create_lucidchart_flowchart(nodes: List[Dict], edges: List[Dict]) -> str:
    """
    Create Lucidchart-compatible flowchart markup from nodes and edges.
    
    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
    
    Returns:
        str: String containing Lucidchart-compatible UML markup for flowcharts
    """
    # Create a mapping of node IDs to readable names
    node_names = {}
    for node in nodes:
        node_id = node["id"]
        node_name = node.get("name", node_id)
        # Clean the name to ensure it works in Lucidchart
        clean_name = re.sub(r'[^\w\s]', '_', node_name)
        node_names[node_id] = clean_name
    
    # Build flowchart lines
    uml_lines = []
    
    # Add header comment
    uml_lines.append("# Lucidchart Flowchart")
    uml_lines.append("# Generated from GraphML file")
    uml_lines.append("")
    
    # First, define all nodes
    for node in nodes:
        node_id = node["id"]
        if node_id not in node_names:
            continue
            
        node_name = node_names[node_id]
        properties = node.get("properties", {})
        
        # Determine node type based on properties or default to process
        node_type = "process"
        
        if "type" in properties:
            node_type_value = properties["type"].lower()
            if "start" in node_type_value or "begin" in node_type_value:
                node_type = "start"
            elif "end" in node_type_value or "stop" in node_type_value:
                node_type = "end"
            elif "decision" in node_type_value or "condition" in node_type_value:
                node_type = "decision"
            elif "input" in node_type_value or "output" in node_type_value:
                node_type = "io"
        
        # Add node definition
        uml_lines.append(f"{node_name}[{node_type}]")
    
    uml_lines.append("")
    
    # Process edges to create connections
    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]
        
        # Skip if source or target not in our nodes
        if source_id not in node_names or target_id not in node_names:
            continue
        
        source_name = node_names[source_id]
        target_name = node_names[target_id]
        
        # Get edge label if any
        label = ""
        if "label" in edge:
            label = edge["label"]
        else:
            for prop_key in ["cond", "label", "condition"]:
                if prop_key in edge.get("properties", {}):
                    label = edge["properties"][prop_key]
                    break
        
        # Create the connection line
        if label:
            uml_lines.append(f"{source_name} -> {target_name}: {label}")
        else:
            uml_lines.append(f"{source_name} -> {target_name}")
    
    return "\n".join(uml_lines)


def create_lucidchart_csv(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """
    Create Lucidchart-compatible CSV data from nodes and edges.
    
    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
    
    Returns:
        List[Dict]: List of dictionaries representing CSV rows
    """
    # Define CSV headers based on Lucidchart's expected format
    csv_headers = [
        "Id", "Name", "Shape Library", "Page ID", "Contained By", 
        "Line Source", "Line Destination", "Source Arrow", "Destination Arrow",
        "Text Area 1", "Text Area 2", "Text Area 3"
    ]
    
    # Create a row ID counter
    row_id = 1
    
    # Start with the Page row
    csv_rows = [
        {
            "Id": str(row_id),
            "Name": "Page",
            "Shape Library": "",
            "Page ID": "",
            "Contained By": "",
            "Line Source": "",
            "Line Destination": "",
            "Source Arrow": "",
            "Destination Arrow": "",
            "Text Area 1": "Page 1",
            "Text Area 2": "",
            "Text Area 3": ""
        }
    ]
    row_id += 1
    
    # Map to store node ID to CSV row ID for connections
    node_id_to_csv_id = {}
    
    # Process nodes
    for node in nodes:
        node_id = node["id"]
        node_name = node.get("name", node_id)
        properties = node.get("properties", {})
        
        # Determine shape type based on properties or default to Process
        shape_type = "Process"
        
        if "type" in properties:
            node_type_value = properties["type"].lower()
            if "start" in node_type_value or "begin" in node_type_value:
                shape_type = "Terminator"
            elif "end" in node_type_value or "stop" in node_type_value:
                shape_type = "Terminator"
            elif "decision" in node_type_value or "condition" in node_type_value:
                shape_type = "Decision"
            elif "input" in node_type_value or "output" in node_type_value:
                shape_type = "Data"
        
        # Store mapping of GraphML ID to CSV row ID
        node_id_to_csv_id[node_id] = str(row_id)
        
        # Extract useful properties for Text Area fields
        text_area_2 = properties.get("resp", "")
        text_area_3 = properties.get("team", "")
        
        # Create node row
        node_row = {
            "Id": str(row_id),
            "Name": shape_type,
            "Shape Library": "Flowchart Shapes",
            "Page ID": "1",
            "Contained By": "",
            "Line Source": "",
            "Line Destination": "",
            "Source Arrow": "",
            "Destination Arrow": "",
            "Text Area 1": node_name,
            "Text Area 2": text_area_2,
            "Text Area 3": text_area_3
        }
        
        csv_rows.append(node_row)
        row_id += 1
    
    # Process edges
    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]
        
        # Skip if we don't have CSV IDs for source or target
        if source_id not in node_id_to_csv_id or target_id not in node_id_to_csv_id:
            continue
        
        # Get source and target row IDs
        source_csv_id = node_id_to_csv_id[source_id]
        target_csv_id = node_id_to_csv_id[target_id]
        
        # Get edge label if any
        label = ""
        if "label" in edge:
            label = edge["label"]
        else:
            for prop_key in ["cond", "label", "condition"]:
                if prop_key in edge.get("properties", {}):
                    label = edge["properties"][prop_key]
                    break
        
        # Create edge row
        edge_row = {
            "Id": str(row_id),
            "Name": "Line",
            "Shape Library": "",
            "Page ID": "1",
            "Contained By": "",
            "Line Source": source_csv_id,
            "Line Destination": target_csv_id,
            "Source Arrow": "None",
            "Destination Arrow": "Arrow",
            "Text Area 1": label,
            "Text Area 2": "",
            "Text Area 3": ""
        }
        
        csv_rows.append(edge_row)
        row_id += 1
    
    return csv_rows


def write_csv_file(csv_data: List[Dict], output_path: Path) -> None:
    """
    Write data to a CSV file in Lucidchart format.
    
    Args:
        csv_data: List of dictionaries representing CSV rows
        output_path: Path to save the CSV file
    """
    if not csv_data:
        return
    
    # Get field names from first row
    fieldnames = list(csv_data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)


def graphml_to_lucidchart(
    input_path: Union[str, Path], 
    output_path: Optional[Union[str, Path]] = None,
    diagram_type: str = "sequence",
    output_format: str = "uml",
    auto_fix: bool = True
) -> Path:
    """
    Convert a GraphML file to Lucidchart-compatible format.
    
    Args:
        input_path: Path to the GraphML file
        output_path: Path for the output file (defaults to same name with appropriate extension)
        diagram_type: Type of diagram to generate ('sequence' or 'flowchart')
        output_format: Output format ('uml' or 'csv')
        auto_fix: Whether to automatically fix GraphML XML errors
        
    Returns:
        Path: Path to the created output file
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the input file is not a GraphML file
    """
    # Convert to Path objects
    input_path = Path(input_path)
    
    # Validate input
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    if input_path.suffix.lower() != '.graphml':
        raise ValueError(f"Input file is not a GraphML file: {input_path}")
    
    # Determine default extension based on output format
    default_ext = '.csv' if output_format.lower() == 'csv' else '.uml'
    
    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix(default_ext)
    else:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path / f"{input_path.stem}{default_ext}"
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract GraphML data with auto-fixing if enabled
    nodes, edges = extract_graphml_data(input_path, auto_fix)
    
    # Create and write output based on specified format
    if output_format.lower() == 'csv':
        csv_data = create_lucidchart_csv(nodes, edges)
        write_csv_file(csv_data, output_path)
    else:
        # Create UML content based on diagram type
        if diagram_type.lower() == "flowchart":
            uml_content = create_lucidchart_flowchart(nodes, edges)
        else:  # default to sequence diagram
            uml_content = create_lucidchart_sequence_diagram(nodes, edges)
        
        # Write UML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(uml_content)
    
    return output_path


def main() -> int:
    """
    Main function to convert GraphML files to Lucidchart format.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert GraphML files to Lucidchart-compatible format")
    parser.add_argument("input", help="Input GraphML file path")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "-t", "--type", 
        choices=["sequence", "flowchart"], 
        default="sequence",
        help="Type of diagram to generate (default: sequence)"
    )
    parser.add_argument(
        "-f", "--format", 
        choices=["uml", "csv"], 
        default="uml",
        help="Output format (uml for text markup, csv for Lucidchart import) (default: uml)"
    )
    parser.add_argument(
        "--no-fix",
        action="store_true",
        help="Disable automatic fixing of GraphML XML errors"
    )
    
    args = parser.parse_args()
    
    try:
        # Convert GraphML to Lucidchart format with auto-fixing unless disabled
        output_path = graphml_to_lucidchart(
            args.input, 
            args.output, 
            args.type,
            args.format,
            not args.no_fix
        )
        
        print(f"Created Lucidchart-compatible file: {output_path}")
        
        if args.format.lower() == 'csv':
            print("You can import this CSV file into Lucidchart:")
            print("1. Open Lucidchart")
            print("2. Select Import > Import from > CSV")
            print("3. Upload the generated CSV file")
        else:
            print(f"You can copy-paste the UML content into Lucidchart's {args.type} diagram editor.")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())