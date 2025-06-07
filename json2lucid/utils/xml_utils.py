#!/usr/bin/env python3
"""
XML utility functions for handling XML/GraphML files.

This module provides helper functions for parsing, fixing, and processing XML files,
with special handling for GraphML files that contain special characters.
"""

import re
import io
import sys
import xml.etree.ElementTree as ET
import xml.sax
import html
from pathlib import Path
from typing import Tuple, Optional, Union, Dict, List, Any


def escape_special_chars(content: str) -> str:
    """
    Escape special XML characters in a string.
    
    Args:
        content: The XML content to process
        
    Returns:
        str: The XML content with special characters properly escaped
    """
    # First handle the content within tags - this is safer than global replacement
    result_parts = []
    in_tag = False
    tag_start = 0
    
    i = 0
    while i < len(content):
        if content[i:i+4] == "<!--" and not in_tag:
            # Handle XML comments specially
            comment_end = content.find("-->", i)
            if comment_end != -1:
                result_parts.append(content[i:comment_end+3])
                i = comment_end + 3
                continue
                
        elif content[i] == "<" and not in_tag:
            # Starting a tag
            in_tag = True
            result_parts.append(content[tag_start:i])
            tag_start = i
        elif content[i] == ">" and in_tag:
            # Ending a tag
            in_tag = False
            result_parts.append(content[tag_start:i+1])
            tag_start = i + 1
        
        i += 1
    
    # Add any remaining content
    if tag_start < len(content):
        result_parts.append(content[tag_start:])
    
    # Now process content (not tags) for special characters
    processed_parts = []
    for i, part in enumerate(result_parts):
        if i % 2 == 0:  # Content, not tags
            # Replace & with &amp; but not if it's already part of an entity
            part = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', part)
            # Replace other special characters
            part = part.replace("<", "&lt;").replace(">", "&gt;")
        processed_parts.append(part)
    
    return "".join(processed_parts)


def read_file_content(file_path: Union[str, Path]) -> str:
    """
    Read file content safely with multiple encoding attempts.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        str: The content of the file
        
    Raises:
        IOError: If the file cannot be read with any encoding
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    raise IOError(f"Could not read file {file_path} with any of the attempted encodings")


def remove_special_chars(content: str) -> str:
    """
    Remove or replace problematic non-printing characters from XML.
    
    Args:
        content: The XML content to process
        
    Returns:
        str: The XML content with problematic characters removed or replaced
    """
    # Replace common problematic characters
    replacements = {
        '\x00': '',      # Null byte - remove
        '\x01': '',      # Start of Heading - remove
        '\x02': '',      # Start of Text - remove
        '\x03': '',      # End of Text - remove
        '\x04': '',      # End of Transmission - remove
        '\x05': '',      # Enquiry - remove
        '\x06': '',      # Acknowledge - remove
        '\x07': '',      # Bell - remove
        '\x08': '',      # Backspace - remove
        '\x0b': '',      # Vertical Tab - remove
        '\x0c': '',      # Form Feed - remove
        '\x0e': '',      # Shift Out - remove
        '\x0f': '',      # Shift In - remove
        '\x10': '',      # Data Link Escape - remove
        '\x11': '',      # Device Control 1 - remove
        '\x12': '',      # Device Control 2 - remove
        '\x13': '',      # Device Control 3 - remove
        '\x14': '',      # Device Control 4 - remove
        '\x15': '',      # Negative Acknowledge - remove
        '\x16': '',      # Synchronous Idle - remove
        '\x17': '',      # End of Transmission Block - remove
        '\x18': '',      # Cancel - remove
        '\x19': '',      # End of Medium - remove
        '\x1a': '',      # Substitute - remove
        '\x1b': '',      # Escape - remove
        '\x1c': '',      # File Separator - remove
        '\x1d': '',      # Group Separator - remove
        '\x1e': '',      # Record Separator - remove
        '\x1f': '',      # Unit Separator - remove
        '\x7f': '',      # Delete - remove
        '\u200b': '',    # Zero Width Space - remove
        '\u200c': '',    # Zero Width Non-Joiner - remove
        '\u200d': '',    # Zero Width Joiner - remove
        '\u200e': '',    # Left-to-Right Mark - remove
        '\u200f': '',    # Right-to-Left Mark - remove
        '\ufeff': ''     # Byte Order Mark - remove
    }
    
    for char, replacement in replacements.items():
        content = content.replace(char, replacement)
        
    return content


def fix_common_xml_issues(content: str) -> str:
    """
    Fix common XML syntax issues beyond character escaping.
    
    Args:
        content: The XML content to process
        
    Returns:
        str: The XML content with common issues fixed
    """
    # Clean non-printing characters
    content = remove_special_chars(content)
    
    # Fix unclosed XML declaration (missing ?>)
    xml_decl_match = re.match(r'<\?xml[^?>]+(?<!\?)>', content)
    if xml_decl_match:
        decl = xml_decl_match.group(0)
        fixed_decl = decl[:-1] + '?>'
        content = content.replace(decl, fixed_decl)
    
    # Make sure XML declaration is at the start
    if not content.lstrip().startswith('<?xml'):
        # Don't add if already present somewhere else
        if '<?xml' not in content:
            content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    
    # Ensure graphml namespace if not present
    if '<graphml' in content and 'xmlns=' not in content:
        content = content.replace('<graphml', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"')
    
    # Fix mismatched quotes in attributes
    content = re.sub(r'=(["\'])([^"\']*)(?!\1)(\s|>)', r'=\1\2\1\3', content)
    
    # Fix missing end tags
    open_tags = re.findall(r'<([a-zA-Z0-9_]+)[^/>]*>(?!.*</\1>)', content)
    for tag in open_tags:
        if f'</{tag}>' not in content and f'<{tag}' in content:
            content += f'</{tag}>'
    
    # Fix broken entities
    entity_pattern = r'&[^;]+;'
    invalid_entities = re.findall(entity_pattern, content)
    for entity in invalid_entities:
        if entity not in ['&amp;', '&lt;', '&gt;', '&quot;', '&apos;']:
            # Try to fix common issues
            if re.match(r'&[a-zA-Z0-9]+[^;]', entity):
                fixed_entity = entity.rstrip() + ';'
                content = content.replace(entity, fixed_entity)
    
    return content


def safe_parse_xml(file_path: Union[str, Path]) -> ET.Element:
    """
    Safely parse XML file, handling common XML parsing issues.
    
    Args:
        file_path: Path to the XML file
        
    Returns:
        ET.Element: Root element of the parsed XML
        
    Raises:
        ValueError: If the file cannot be parsed after fixing attempts
    """
    file_path = Path(file_path)
    
    # Try direct parsing first
    try:
        tree = ET.parse(file_path)
        return tree.getroot()
    except ET.ParseError as original_error:
        # If direct parsing fails, try pre-processing the file
        try:
            # Read file content
            try:
                content = read_file_content(file_path)
            except IOError as io_err:
                raise ValueError(f"Could not read file: {io_err}")
            
            # Step 1: Try with minimal fixes - just escape special chars
            fixed_content = escape_special_chars(content)
            
            try:
                root = ET.fromstring(fixed_content)
                return root
            except ET.ParseError:
                # Step 2: Apply more aggressive fixes
                fixed_content = fix_common_xml_issues(fixed_content)
                
                try:
                    root = ET.fromstring(fixed_content)
                    return root
                except ET.ParseError as final_error:
                    # If still can't parse, provide detailed error information
                    line_num, column = getattr(final_error, 'position', (0, 0))
                    
                    # Try to show context around the error
                    lines = fixed_content.splitlines()
                    error_context = ""
                    if 0 <= line_num - 1 < len(lines):
                        if line_num > 1:
                            error_context += f"Line {line_num-1}: {lines[line_num-2]}\n"
                        error_context += f"Line {line_num}: {lines[line_num-1]}\n"
                        error_context += " " * (column + 8) + "^ Error occurs near here\n"
                        if line_num < len(lines):
                            error_context += f"Line {line_num+1}: {lines[line_num]}\n"
                    
                    raise ValueError(
                        f"Failed to parse XML file: {final_error}\n"
                        f"Error location: Line {line_num}, Column {column}\n"
                        f"{error_context}"
                    )
                    
        except Exception as fix_error:
            # If fixing fails, provide detailed error information
            line_num, column = getattr(original_error, 'position', (0, 0))
            error_details = _get_xml_error_details(file_path, line_num, column)
            
            error_message = (
                f"Failed to parse XML file: {original_error}\n"
                f"Error location: Line {line_num}, Column {column}\n"
                f"{error_details}"
            )
            raise ValueError(error_message)


def _get_xml_error_details(file_path: Path, line_num: int, column: int) -> str:
    """
    Get details about the XML error location in the file.
    
    Args:
        file_path: Path to the XML file
        line_num: Line number where the error occurred
        column: Column number where the error occurred
        
    Returns:
        str: Formatted error details
    """
    try:
        content = read_file_content(file_path)
        lines = content.splitlines()
        
        if 0 <= line_num - 1 < len(lines):
            problem_line = lines[line_num - 1]
            line_info = f"Line {line_num}: {problem_line}\n"
            pointer = " " * (column + 8) + "^ Error occurs near here\n"
            
            # Try to identify common XML issues
            diagnosis = []
            if '&' in problem_line and not re.search(r'&(amp|lt|gt|quot|apos);', problem_line):
                diagnosis.append("Unescaped '&' character. Replace with '&amp;'")
            if problem_line.count('<') != problem_line.count('>'):
                diagnosis.append("Mismatched angle brackets '<' and '>'")
            if problem_line.count('"') % 2 != 0:
                diagnosis.append("Unclosed quote")
            if problem_line.count("'") % 2 != 0:
                diagnosis.append("Unclosed single quote")
            if '<?xml' in problem_line and '?>' not in problem_line:
                diagnosis.append("Unclosed XML declaration")
            
            diagnosis_info = ""
            if diagnosis:
                diagnosis_info = "Possible issues:\n- " + "\n- ".join(diagnosis)
            
            return f"{line_info}{pointer}{diagnosis_info}"
        return "Could not retrieve the problem line."
    except Exception:
        return "Could not analyze the error location."


def fix_xml_file(input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Fix common XML formatting issues in a file.
    
    Args:
        input_path: Path to the input XML file
        output_path: Path for the output fixed XML file (defaults to creating a backup and overwriting input)
        
    Returns:
        Path: Path to the fixed XML file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        IOError: If there's an error reading or writing the files
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # If no output path specified, create a backup and overwrite the original
    if output_path is None:
        backup_path = input_path.with_suffix(f"{input_path.suffix}.bak")
        output_path = input_path
    else:
        backup_path = None
        output_path = Path(output_path)
    
    try:
        # Read the input file
        content = read_file_content(input_path)
        
        # Create backup if needed
        if backup_path:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Apply fixes in stages for better tracking
        
        # Stage 1: Basic escaping of special characters
        fixed_content = escape_special_chars(content)
        
        # Stage 2: Additional XML syntax fixes
        fixed_content = fix_common_xml_issues(fixed_content)
        
        # Try to validate the fixes by parsing
        try:
            ET.fromstring(fixed_content)
        except ET.ParseError as e:
            # If still fails, apply a more aggressive approach
            line_num, column = getattr(e, 'position', (0, 0))
            print(f"Warning: Fixes did not resolve all issues. Error at line {line_num}, column {column}")
            print("Applying more aggressive fixes...")
            
            # Convert to plain text and back to XML to try to handle encoding issues
            # This may change formatting but should preserve semantic content
            fixed_content = html.unescape(html.escape(fixed_content))
            
            # Try one more time with regex-based fixes for specific line
            if 0 <= line_num - 1 < len(fixed_content.splitlines()):
                lines = fixed_content.splitlines()
                problem_line = lines[line_num - 1]
                
                # Try to fix problematic line
                fixed_line = problem_line
                
                # Handle specific issues
                if '&' in fixed_line:
                    fixed_line = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', fixed_line)
                    
                # Replace the line
                lines[line_num - 1] = fixed_line
                fixed_content = '\n'.join(lines)
        
        # Write the fixed content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
            
        return output_path
    
    except Exception as e:
        raise IOError(f"Error fixing XML file: {e}")


def get_xml_namespaces(root: ET.Element) -> Tuple[dict, str]:
    """
    Extract XML namespaces from the root element.
    
    Args:
        root: Root element of an XML document
        
    Returns:
        Tuple[dict, str]: Dictionary of namespaces and namespace prefix string
    """
    # Handle namespace if present
    ns = {}
    ns_prefix = ""
    
    if root.tag and "}" in root.tag:
        ns_uri = root.tag.split("}")[0].strip("{")
        ns = {"": ns_uri}
        ns_prefix = "{" + ns_uri + "}"
    
    # Also check for explicitly defined namespaces
    for key, value in root.attrib.items():
        if key.startswith('xmlns:'):
            prefix = key.split(':')[1]
            ns[prefix] = value
        elif key == 'xmlns':
            ns[""] = value
            ns_prefix = "{" + value + "}"
    
    return ns, ns_prefix


def validate_graphml(root: ET.Element) -> Tuple[bool, List[str]]:
    """
    Validate basic GraphML structure.
    
    Args:
        root: Root element of the XML document
        
    Returns:
        Tuple[bool, List[str]]: Validation status and list of error messages
    """
    errors = []
    
    # Check for required elements
    required_elements = {
        'graphml': False,
        'graph': False
    }
    
    # Handle namespaces
    ns, ns_prefix = get_xml_namespaces(root)
    
    # Check root element
    if root.tag == f"{ns_prefix}graphml" or root.tag == "graphml":
        required_elements['graphml'] = True
    else:
        errors.append(f"Root element is not 'graphml', found: {root.tag}")
    
    # Check for graph element
    graph_element = root.find(f".//{ns_prefix}graph") or root.find(".//graph")
    if graph_element is not None:
        required_elements['graph'] = True
    else:
        errors.append("No 'graph' element found")
    
    # Validate basic structure
    is_valid = all(required_elements.values())
    
    return is_valid, errors