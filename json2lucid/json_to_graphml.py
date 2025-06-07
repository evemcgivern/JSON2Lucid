#!/usr/bin/env python3
"""
Convert JSON workflow definitions to GraphML format.

This module transforms JSON workflow definitions into GraphML XML format
that can be used with graph visualization tools or converted to other formats.
"""

import json
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple

def create_graphml_base() -> ET.Element:
    """
    Create the base GraphML XML structure with required namespaces and keys.
    
    Returns:
        ET.Element: Root GraphML element with namespaces and key definitions
    """
    # Create the root element with namespaces
    graphml = ET.Element('graphml')
    graphml.set('xmlns', 'http://graphml.graphdrawing.org/xmlns')
    graphml.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    graphml.set('xmlns:y', 'http://www.yworks.com/xml/graphml')
    graphml.set('xsi:schemaLocation', 'http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd')
    
    # Define node property keys
    keys = [
        ('d0', 'node', 'label', 'string'),
        ('d1', 'node', 'type', 'string'),
        ('d2', 'node', 'desc', 'string'),
        ('d3', 'node', 'team', 'string'),
        ('d4', 'node', 'resp', 'string'),
        ('d5', 'node', 'crit', 'string'),
        ('e0', 'edge', 'label', 'string'),
        ('e1', 'edge', 'cond', 'string')
    ]
    
    for key_id, for_type, attr_name, attr_type in keys:
        key = ET.SubElement(graphml, 'key')
        key.set('id', key_id)
        key.set('for', for_type)
        key.set('attr.name', attr_name)
        key.set('attr.type', attr_type)
    
    return graphml

def sanitize_id(identifier: str) -> str:
    """
    Sanitize node or edge IDs to be valid in GraphML.
    
    Args:
        identifier: Original identifier that might contain invalid characters
        
    Returns:
        str: Sanitized identifier safe for use in GraphML
    """
    if not identifier:
        return "node_unknown"
        
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(identifier))
    
    # Ensure it starts with a letter or underscore (GraphML requirement)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"n_{sanitized}"
        
    return sanitized

def create_graph_node(
    graph: ET.Element, 
    node_id: str, 
    label: str, 
    node_type: str = "default",
    description: str = "", 
    team: str = "", 
    responsibilities: str = "",
    criteria: str = ""
) -> ET.Element:
    """
    Create a node element in the GraphML graph.
    
    Args:
        graph: Parent graph element
        node_id: Unique identifier for the node
        label: Display label for the node
        node_type: Type classification (start, end, process, decision, etc.)
        description: Detailed description of the node
        team: Responsible team
        responsibilities: Core responsibilities
        criteria: Completion criteria
        
    Returns:
        ET.Element: The created node element
    """
    # Create node with sanitized ID
    safe_id = sanitize_id(node_id)
    node = ET.SubElement(graph, 'node')
    node.set('id', safe_id)
    
    # Add node properties as data elements
    if label:
        data_label = ET.SubElement(node, 'data')
        data_label.set('key', 'd0')
        data_label.text = label
    
    if node_type:
        data_type = ET.SubElement(node, 'data')
        data_type.set('key', 'd1')
        data_type.text = node_type
        
    if description:
        data_desc = ET.SubElement(node, 'data')
        data_desc.set('key', 'd2')
        data_desc.text = description
        
    if team:
        data_team = ET.SubElement(node, 'data')
        data_team.set('key', 'd3')
        data_team.text = team
        
    if responsibilities:
        data_resp = ET.SubElement(node, 'data')
        data_resp.set('key', 'd4')
        data_resp.text = responsibilities
        
    if criteria:
        data_crit = ET.SubElement(node, 'data')
        data_crit.set('key', 'd5')
        data_crit.text = criteria
    
    return node

def create_graph_edge(
    graph: ET.Element, 
    source_id: str, 
    target_id: str, 
    label: str = "",
    condition: str = ""
) -> ET.Element:
    """
    Create an edge element connecting nodes in the GraphML graph.
    
    Args:
        graph: Parent graph element
        source_id: ID of the source node
        target_id: ID of the target node
        label: Display label for the edge
        condition: Condition for this transition
        
    Returns:
        ET.Element: The created edge element
    """
    # Create edge with sanitized IDs
    safe_source = sanitize_id(source_id)
    safe_target = sanitize_id(target_id)
    
    edge = ET.SubElement(graph, 'edge')
    edge.set('source', safe_source)
    edge.set('target', safe_target)
    
    # Add edge label if provided
    if label:
        data_label = ET.SubElement(edge, 'data')
        data_label.set('key', 'e0')
        data_label.text = label
        
    # Add condition if provided
    if condition:
        data_cond = ET.SubElement(edge, 'data')
        data_cond.set('key', 'e1')
        data_cond.text = condition
    
    return edge

def json_to_graphml_object(json_data: Dict[str, Any]) -> ET.Element:
    """
    Convert JSON workflow definition to GraphML XML element tree.
    
    Args:
        json_data: JSON workflow data as a Python dictionary
        
    Returns:
        ET.Element: Root GraphML element with complete graph structure
    """
    # Create the base GraphML structure
    graphml = create_graphml_base()
    
    # Create the graph element
    graph = ET.SubElement(graphml, 'graph')
    graph.set('id', 'G')
    graph.set('edgedefault', 'directed')
    
    # Check if the JSON has the expected structure
    if not isinstance(json_data, dict) or 'flow' not in json_data:
        raise ValueError("Invalid JSON format: Missing 'flow' element")
    
    flow = json_data['flow']
    
    # Create a start node for the entry condition if one exists
    if 'entry_condition' in flow and flow['entry_condition']:
        entry_node_id = "start"
        create_graph_node(
            graph, 
            entry_node_id, 
            "Start", 
            node_type="start",
            description=flow['entry_condition']
        )
        
        # Keep track of whether we've connected the start node
        start_connected = False
    else:
        start_connected = True  # Skip start node if no entry condition
    
    # Process nodes
    node_id_mapping = {}  # Maps original IDs to sanitized ones
    
    if 'nodes' not in flow or not isinstance(flow['nodes'], list):
        raise ValueError("Invalid JSON format: Missing or invalid 'nodes' array")
    
    for node_data in flow['nodes']:
        if not isinstance(node_data, dict) or 'id' not in node_data:
            continue  # Skip invalid nodes
            
        node_id = node_data['id']
        label = node_data.get('name', node_id)
        entry_condition = node_data.get('entry_condition', '')
        responsible_team = node_data.get('responsible_team', '')
        core_responsibilities = node_data.get('core_responsibilities', '')
        completion_criteria = node_data.get('completion_criteria', '')
        
        # Create the node
        node_element = create_graph_node(
            graph,
            node_id,
            label,
            node_type="process",
            description=entry_condition,
            team=responsible_team,
            responsibilities=core_responsibilities,
            criteria=completion_criteria
        )
        
        # Store the mapping of original ID to sanitized ID
        node_id_mapping[node_id] = node_element.get('id')
        
        # Connect start node to the first node if not connected yet
        if not start_connected and 'entry_condition' in flow:
            create_graph_edge(
                graph,
                "start",
                node_id,
                condition=flow['entry_condition']
            )
            start_connected = True
    
    # Process edges from the explicit edges section if it exists
    if 'edges' in flow and isinstance(flow['edges'], list):
        for edge_data in flow['edges']:
            if not isinstance(edge_data, dict) or 'from' not in edge_data or 'to' not in edge_data:
                continue  # Skip invalid edges
                
            source_id = edge_data['from']
            target_id = edge_data['to']
            condition = edge_data.get('condition', '')
            
            # Create the edge using sanitized IDs
            create_graph_edge(
                graph,
                source_id,
                target_id,
                condition=condition
            )
    
    # Process implicit edges from next_handoff_destinations if no explicit edges
    elif 'nodes' in flow and isinstance(flow['nodes'], list):
        for node_data in flow['nodes']:
            if not isinstance(node_data, dict) or 'id' not in node_data:
                continue
                
            source_id = node_data['id']
            
            # Check for next_handoff_destinations
            if 'next_handoff_destinations' in node_data and isinstance(node_data['next_handoff_destinations'], list):
                for target_id in node_data['next_handoff_destinations']:
                    # Create edge
                    create_graph_edge(graph, source_id, target_id)
    
    return graphml

def convert_json_to_graphml(
    input_path: Union[str, Path], 
    output_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Convert a JSON workflow file to GraphML format.
    
    Args:
        input_path: Path to the JSON input file
        output_path: Path for the GraphML output file (optional)
        
    Returns:
        Path: Path to the created GraphML file
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the JSON is invalid or doesn't have the expected structure
    """
    # Convert to Path objects
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Determine output path if not specified
    if output_path is None:
        output_path = input_path.with_suffix('.graphml')
    else:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path / f"{input_path.stem}.graphml"
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load JSON
    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            json_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    # Convert to GraphML
    graphml_root = json_to_graphml_object(json_data)
    
    # Write GraphML file
    tree = ET.ElementTree(graphml_root)
    
    # Check if ET.indent is available (Python 3.9+)
    if hasattr(ET, 'indent'):
        ET.indent(tree, space="  ")  # Pretty print the XML
    
    with open(output_path, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)
    
    return output_path

def main() -> int:
    """
    Command-line interface for the JSON to GraphML converter.
    
    Returns:
        int: Exit code (0 for success)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert JSON workflow definitions to GraphML format")
    parser.add_argument(
        "input", 
        help="Input JSON workflow file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output GraphML file (default: input_filename.graphml)"
    )
    
    args = parser.parse_args()
    
    try:
        output_path = convert_json_to_graphml(args.input, args.output)
        print(f"Successfully created GraphML file: {output_path}")
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())