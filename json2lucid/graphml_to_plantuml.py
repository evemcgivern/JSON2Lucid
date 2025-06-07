#!/usr/bin/env python3
"""
Convert GraphML files to PlantUML format.

This script transforms GraphML files into PlantUML notation,
preserving node information and relationships. It automatically
handles common XML parsing issues in GraphML files.
"""

import os
import sys
import xml.etree.ElementTree as ET
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Set, Any

# Import our XML utilities from utils directory
from utils.xml_utils import safe_parse_xml, get_xml_namespaces, fix_xml_file


def extract_graphml_data(graphml_file: Path, auto_fix: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract nodes and edges data from a GraphML file.
    
    Args:
        graphml_file: Path to the GraphML file
        auto_fix: Whether to automatically attempt to fix XML parsing errors
        
    Returns:
        Tuple containing lists of node and edge dictionaries
    """
    try:
        # Try to parse the GraphML file directly
        root = safe_parse_xml(graphml_file)
        
    except ValueError as e:
        if auto_fix:
            # If parsing fails and auto_fix is enabled, try to fix the file
            print(f"XML parsing error: {e}")
            print("Attempting to fix GraphML file...")
            
            # Create a temporary fixed file
            fixed_file = graphml_file.with_name(f"{graphml_file.stem}_fixed_temp{graphml_file.suffix}")
            try:
                fix_xml_file(graphml_file, fixed_file)
                print(f"Created fixed file: {fixed_file}")
                
                # Try parsing the fixed file
                root = safe_parse_xml(fixed_file)
                print("Successfully parsed fixed GraphML file")
                
            except Exception as fix_err:
                # If fixing fails, clean up and re-raise
                if fixed_file.exists():
                    fixed_file.unlink()  # Delete the temporary file
                print(f"Failed to fix GraphML file: {fix_err}")
                raise
            
            finally:
                # Clean up temporary file if exists
                if fixed_file.exists():
                    fixed_file.unlink()
        else:
            # If auto_fix is disabled, re-raise the error
            raise
    
    try:
        # Handle namespace if present
        ns, ns_prefix = get_xml_namespaces(root)
        
        # Find all nodes and their properties
        nodes = []
        # Fix: Use 'is not None' instead of truth value testing
        graph_elem_ns = root.find(f".//{ns_prefix}graph")
        graph_element = graph_elem_ns if graph_elem_ns is not None else root.find(".//graph")
        
        if graph_element is None:
            raise ValueError("Could not find graph element in the GraphML file")
            
        # Process nodes - Fix: Use 'is not None' for element tests
        node_elems_ns = graph_element.findall(f"./{ns_prefix}node")
        node_elems = node_elems_ns if node_elems_ns else graph_element.findall("./node")
        
        for node_elem in node_elems:
            node_id = node_elem.get('id')
            node_info = {"id": node_id, "properties": {}}
            
            # Extract node data
            data_elems_ns = node_elem.findall(f"./{ns_prefix}data")
            data_elems = data_elems_ns if data_elems_ns else node_elem.findall("./data")
            
            for data_elem in data_elems:
                key = data_elem.get('key')
                value = data_elem.text or ""
                node_info["properties"][key] = value
                
                # Use label as name if available
                if key == "label":
                    node_info["name"] = value
            
            # Default to ID if no label
            if "name" not in node_info:
                node_info["name"] = node_id
                
            nodes.append(node_info)
        
        # Find all edges
        edges = []
        edge_elems_ns = graph_element.findall(f"./{ns_prefix}edge")
        edge_elems = edge_elems_ns if edge_elems_ns else graph_element.findall("./edge")
        
        for edge_elem in edge_elems:
            edge_id = edge_elem.get('id') or ""
            source = edge_elem.get('source')
            target = edge_elem.get('target')
            
            if not source or not target:
                continue
                
            edge_info = {
                "id": edge_id,
                "source": source,
                "target": target,
                "properties": {}
            }
            
            # Extract edge data - Get data elements from edge
            edge_data_elems_ns = edge_elem.findall(f"./{ns_prefix}data")
            edge_data_elems = edge_data_elems_ns if edge_data_elems_ns else edge_elem.findall("./data")
            
            for data_elem in edge_data_elems:
                key = data_elem.get('key')
                value = data_elem.text or ""
                edge_info["properties"][key] = value
                
            edges.append(edge_info)
        
        return nodes, edges
    
    except Exception as e:
        print(f"Error processing GraphML file structure: {e}")
        sys.exit(1)


def create_plantuml_class_diagram(nodes: List[Dict], edges: List[Dict]) -> str:
    """
    Create PlantUML class diagram notation from nodes and edges.
    
    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
    
    Returns:
        String containing PlantUML class diagram notation
    """
    plantuml_lines = ["@startuml", ""]
    
    # Configure the diagram
    plantuml_lines.append("' PlantUML Class Diagram")
    plantuml_lines.append("' Generated from GraphML")
    plantuml_lines.append("skinparam shadowing false")
    plantuml_lines.append("skinparam classAttributeIconSize 0")
    plantuml_lines.append("skinparam monochrome false")
    plantuml_lines.append("skinparam packageStyle rectangle")
    plantuml_lines.append("skinparam defaultFontName Arial")
    plantuml_lines.append("skinparam defaultFontSize 12")
    plantuml_lines.append("")
    
    # Define nodes as classes
    for node in nodes:
        node_id = node["id"]
        node_name = node.get("name", node_id)
        
        # Start class definition
        plantuml_lines.append(f"class \"{node_name}\" as {node_id} {{")
        
        # Add properties as class attributes
        for key, value in node.get("properties", {}).items():
            if key != "label":  # Skip label as it's already the class name
                safe_value = value.replace("\n", "\\n") if value else ""
                plantuml_lines.append(f"  +{key}: {safe_value}")
                
        # End class definition
        plantuml_lines.append("}")
        plantuml_lines.append("")
    
    # Define relationships
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        
        # Get edge label if any
        label = edge.get("properties", {}).get("cond", "")
        if label:
            plantuml_lines.append(f"{source} --> {target} : {label}")
        else:
            plantuml_lines.append(f"{source} --> {target}")
    
    plantuml_lines.append("")
    plantuml_lines.append("@enduml")
    
    return "\n".join(plantuml_lines)


def create_plantuml_activity_diagram(nodes: List[Dict], edges: List[Dict]) -> str:
    """
    Create PlantUML activity diagram notation from nodes and edges.
    
    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
    
    Returns:
        String containing PlantUML activity diagram notation
    """
    plantuml_lines = ["@startuml", ""]
    
    # Configure the diagram
    plantuml_lines.append("' PlantUML Activity Diagram")
    plantuml_lines.append("' Generated from GraphML")
    plantuml_lines.append("skinparam shadowing false")
    plantuml_lines.append("skinparam monochrome false")
    plantuml_lines.append("skinparam defaultFontName Arial")
    plantuml_lines.append("skinparam defaultFontSize 12")
    plantuml_lines.append("skinparam ActivityBackgroundColor #FEFECE")
    plantuml_lines.append("skinparam ActivityBorderColor #000000")
    plantuml_lines.append("")
    
    # Create a map of node IDs to safe names for PlantUML
    id_to_name = {}
    for node in nodes:
        node_id = node["id"]
        safe_id = f"act_{node_id}"
        id_to_name[node_id] = safe_id
        
        # Define activity
        node_name = node.get("name", node_id)
        team = node.get("properties", {}).get("team", "")
        
        if team:
            display_name = f"{node_name}\\n({team})"
        else:
            display_name = node_name
            
        plantuml_lines.append(f":{display_name};")
    
    # Add connections between activities
    processed_edges = set()  # Track edges to avoid duplicates
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        edge_key = f"{source}->{target}"
        
        if edge_key in processed_edges:
            continue
            
        processed_edges.add(edge_key)
        
        # Get edge label if any
        label = edge.get("properties", {}).get("cond", "")
        if label:
            plantuml_lines.append(f"-> {label};")
        
        source_name = id_to_name.get(source, "")
        target_name = id_to_name.get(target, "")
        
        plantuml_lines.append("")
    
    plantuml_lines.append("")
    plantuml_lines.append("@enduml")
    
    return "\n".join(plantuml_lines)


def graphml_to_plantuml(
    input_path: Union[str, Path], 
    output_path: Optional[Union[str, Path]] = None,
    diagram_type: str = "class",
    auto_fix: bool = True
) -> Path:
    """
    Convert a GraphML file to PlantUML format.
    
    Args:
        input_path: Path to the GraphML file
        output_path: Path for the output PlantUML file (defaults to same name with .puml extension)
        diagram_type: Type of diagram to generate ('class' or 'activity')
        auto_fix: Whether to automatically fix GraphML XML errors
        
    Returns:
        Path to the created PlantUML file
    """
    # Convert to Path objects
    input_path = Path(input_path)
    
    # Validate input
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    if input_path.suffix.lower() != '.graphml':
        raise ValueError(f"Input file is not a GraphML file: {input_path}")
    
    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix('.puml')
    else:
        output_path = Path(output_path)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract GraphML data with auto-fixing if enabled
    nodes, edges = extract_graphml_data(input_path, auto_fix)
    
    # Create PlantUML content based on specified diagram type
    if diagram_type.lower() == "activity":
        plantuml_content = create_plantuml_activity_diagram(nodes, edges)
    else:  # default to class diagram
        plantuml_content = create_plantuml_class_diagram(nodes, edges)
    
    # Write PlantUML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(plantuml_content)
    
    return output_path


def generate_diagram_image(puml_path: Path, output_format: str = "png") -> Path:
    """
    Generate an image from a PlantUML file.
    
    Args:
        puml_path: Path to the PlantUML file
        output_format: Output image format (png, svg, pdf, etc.)
        
    Returns:
        Path to the generated image file
    """
    # Check if PlantUML JAR is available
    plantuml_jar = os.environ.get("PLANTUML_JAR")
    if not plantuml_jar:
        plantuml_jar = str(Path(__file__).parent / "plantuml.jar")
        if not Path(plantuml_jar).exists():
            print("PlantUML JAR not found. Please download it from http://plantuml.com/download")
            print("and set the PLANTUML_JAR environment variable or place it in the same directory as this script.")
            return None
    
    # Determine output path
    output_path = puml_path.with_suffix(f".{output_format}")
    
    # Generate diagram image
    try:
        cmd = ["java", "-jar", plantuml_jar, "-t" + output_format, str(puml_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.SubprocessError as e:
        print(f"Error generating diagram image: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def verify_graphml_file(graphml_file: Path) -> Dict[str, Any]:
    """
    Verify a GraphML file and return diagnostic information.
    
    This function is useful for debugging GraphML parsing issues.
    
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
    
    try:
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
            
        # Try to parse
        tree = ET.parse(graphml_file)
        root = tree.getroot()
        diagnostics["can_parse"] = True
        
        # Count nodes and edges
        ns, ns_prefix = get_xml_namespaces(root)
        
        graph_elem_ns = root.find(f".//{ns_prefix}graph")
        graph_elem = graph_elem_ns if graph_elem_ns is not None else root.find(".//graph")
        
        if graph_elem is not None:
            nodes_ns = graph_elem.findall(f"./{ns_prefix}node")
            nodes = nodes_ns if nodes_ns else graph_elem.findall("./node")
            
            edges_ns = graph_elem.findall(f"./{ns_prefix}edge") 
            edges = edges_ns if edges_ns else graph_elem.findall("./edge")
            
            diagnostics["node_count"] = len(nodes)
            diagnostics["edge_count"] = len(edges)
        
    except ET.ParseError as e:
        diagnostics["parse_errors"] = str(e)
    except Exception as e:
        diagnostics["parse_errors"] = f"Unexpected error: {str(e)}"
        
    return diagnostics


def main() -> int:
    """
    Main function to convert GraphML files to PlantUML format.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert GraphML files to PlantUML format")
    parser.add_argument("input", help="Input GraphML file path")
    parser.add_argument("-o", "--output", help="Output PlantUML file path")
    parser.add_argument(
        "-t", "--type", 
        choices=["class", "activity"], 
        default="class",
        help="Type of UML diagram to generate (default: class)"
    )
    parser.add_argument(
        "-i", "--image",
        action="store_true",
        help="Generate diagram image using PlantUML"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["png", "svg", "pdf"],
        default="png",
        help="Output image format when using --image (default: png)"
    )
    parser.add_argument(
        "--no-fix",
        action="store_true",
        help="Disable automatic fixing of GraphML XML errors"
    )
    parser.add_argument(
        "--fix-only",
        action="store_true",
        help="Only fix GraphML file without converting to PlantUML"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the GraphML file structure without conversion"
    )
    
    args = parser.parse_args()
    
    try:
        # Verify mode for debugging
        if args.verify:
            from utils.xml_utils import verify_graphml_file
            diagnostics = verify_graphml_file(Path(args.input))
            print("GraphML File Diagnostics:")
            for key, value in diagnostics.items():
                print(f"  {key}: {value}")
            return 0
            
        if args.fix_only:
            # Just fix the GraphML file and save it
            fixed_path = fix_xml_file(args.input, args.output)
            print(f"Fixed GraphML file saved to: {fixed_path}")
            return 0
        
        # Convert GraphML to PlantUML with auto-fixing unless disabled
        puml_path = graphml_to_plantuml(
            args.input, 
            args.output, 
            args.type,
            not args.no_fix
        )
        print(f"Created PlantUML file: {puml_path}")
        
        # Generate diagram image if requested
        if args.image:
            img_path = generate_diagram_image(puml_path, args.format)
            if img_path:
                print(f"Generated diagram image: {img_path}")
            else:
                print("Failed to generate diagram image")
                return 1
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())