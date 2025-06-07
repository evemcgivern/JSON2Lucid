"""
Create a simple icon for the JSON2Lucid application.
This script generates an icon file that visually represents the
JSON2Lucid format conversion functionality with a JSON icon,
an arrow, and a Lucid icon.
"""

import os
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests

def download_icon(url: str) -> Image.Image:
    """
    Download an icon from the provided URL.
    
    Args:
        url: The URL to download the icon from
        
    Returns:
        Image.Image: The downloaded icon as a PIL Image object or None if download failed
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except (requests.RequestException, IOError) as e:
        print(f"Failed to download icon from {url}: {e}")
        return None

def load_json_icon(file_path: str = "utils/json-9-48.png") -> Image.Image:
    """
    Load the JSON icon from the local file system.
    
    Args:
        file_path: Path to the JSON icon file
        
    Returns:
        Image.Image: The loaded JSON icon as a PIL Image object or None if loading failed
    """
    try:
        # Convert to absolute path if it's a relative path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"JSON icon file not found at {file_path}")
            return None
            
        # Load and return the image
        return Image.open(file_path).convert("RGBA")
    except IOError as e:
        print(f"Failed to load JSON icon from {file_path}: {e}")
        return None

def load_lucid_icon(file_path: str = "utils//lucid-icon.png") -> Image.Image:
    """
    Load the Lucid icon from the local file system.
    
    Args:
        file_path: Path to the Lucid icon file
        
    Returns:
        Image.Image: The loaded Lucid icon as a PIL Image object or None if loading failed
    """
    try:
        # Convert to absolute path if it's a relative path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Lucid icon file not found at {file_path}")
            return None
            
        # Load and return the image
        return Image.open(file_path).convert("RGBA")
    except IOError as e:
        print(f"Failed to load Lucid icon from {file_path}: {e}")
        return None

def create_icon(output_path: str = "utils/icon.ico") -> None:
    """
    Create an icon for the JSON2Lucid application showing conversion
    from JSON to Lucid formats with a diagonal flow.
    
    Args:
        output_path: Path where the icon file will be saved
        
    Returns:
        None
    """
    # Create a 256x256 image with transparent background
    img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    json_green = (67, 176, 42)     # Green for JSON
    lucid_orange = (255, 127, 42)  # Orange for Lucid logo
    white = (255, 255, 255)        # White
    arrow_color = (50, 50, 150)    # Blue for arrow
    
    # Try to load the JSON icon from local file
    json_icon = load_json_icon()
    
    # If JSON icon loading succeeded, resize and paste it in upper left quadrant
    if json_icon:
        # Resize the JSON icon to fit upper-left quadrant
        json_size = (80, 80)
        json_icon = json_icon.resize(json_size, Image.LANCZOS)
        # Paste the JSON icon in the upper left
        img.paste(json_icon, (20, 20), json_icon)
    else:
        # Fallback: Draw our own JSON icon if loading failed
        # Rounded rectangle for JSON in upper left quadrant
        json_rect = [(10, 10), (110, 110)]
        draw.rounded_rectangle(json_rect, radius=10, fill=json_green)
        
        # Add code brackets to JSON icon
        bracket_color = white
        # Left bracket
        draw.line([(30, 35), (20, 60), (30, 85)], fill=bracket_color, width=3)
        # Right bracket
        draw.line([(90, 35), (100, 60), (90, 85)], fill=bracket_color, width=3)
        # Two dots (representing JSON dots)
        draw.ellipse([(45, 55), (55, 65)], fill=bracket_color)
        draw.ellipse([(65, 55), (75, 65)], fill=bracket_color)
        
        # Add "json" text
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except IOError:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 18)
            except IOError:
                font = ImageFont.load_default()
        
        draw.text((35, 75), "json", fill=white, font=font)
    
    # Draw thick diagonal arrow from upper left to lower right
    # Calculate arrow points for a diagonal arrow
    start_x, start_y = 95, 95  # Starting near the JSON icon
    end_x, end_y = 150, 150    # Ending near the Lucid icon
    
    # Arrow width
    arrow_width = 10
    
    # Draw thick arrow line
    draw.line([(start_x, start_y), (end_x, end_y)], fill=arrow_color, width=arrow_width)
    
    # Draw arrow head (triangle)
    # Calculate the angle of the arrow
    import math
    angle = math.atan2(end_y - start_y, end_x - start_x)
    
    # Calculate the points for the arrowhead
    arrow_head_length = 25
    arrow_head_width = 20
    
    # Calculate points for the arrow head
    point1_x = end_x
    point1_y = end_y
    
    point2_x = int(end_x - arrow_head_length * math.cos(angle) + arrow_head_width * math.sin(angle))
    point2_y = int(end_y - arrow_head_length * math.sin(angle) - arrow_head_width * math.cos(angle))
    
    point3_x = int(end_x - arrow_head_length * math.cos(angle) - arrow_head_width * math.sin(angle))
    point3_y = int(end_y - arrow_head_length * math.sin(angle) + arrow_head_width * math.cos(angle))
    
    arrow_head_points = [(point1_x, point1_y), (point2_x, point2_y), (point3_x, point3_y)]
    draw.polygon(arrow_head_points, fill=arrow_color)
    
    # Try to load the Lucid icon from local file
    lucid_icon = load_lucid_icon()
    
    # If Lucid icon loading succeeded, resize and paste it in lower right quadrant
    if lucid_icon:
        # Resize the Lucid icon to fit lower-right quadrant
        lucid_size = (80, 80)
        lucid_icon = lucid_icon.resize(lucid_size, Image.LANCZOS)
        # Paste the Lucid icon in the lower right
        img.paste(lucid_icon, (156, 156), lucid_icon)
    else:
        # Fallback: Draw our own Lucid icon if loading failed
        # Draw the isometric "L" in lower right quadrant
        l_points = [
            (160, 200),  # Bottom of vertical bar
            (160, 160),  # Top of vertical bar
            (180, 170),  # Top-right of vertical bar
            (180, 210),  # Bottom-right of vertical bar
            (160, 200),  # Back to bottom of vertical
            (200, 220),  # Bottom-right of horizontal
            (220, 210),  # Far right of horizontal
            (180, 190),  # Top-right connection
            (180, 210)   # Back to bottom-right of vertical
        ]
        draw.polygon(l_points, fill=lucid_orange)
        
        # Draw shadow/3D effect for Lucid L
        shadow_points = [
            (160, 200),  # Bottom of vertical
            (180, 210),  # Bottom-right of vertical
            (200, 220),  # Bottom of horizontal
            (180, 210)   # Connect back
        ]
        draw.polygon(shadow_points, fill=(200, 100, 30))  # Darker orange shadow
    
    # Convert string path to Path object for better path handling
    output_path = Path(output_path)
    
    # Ensure the utils directory exists
    utils_dir = Path("utils")
    utils_dir.mkdir(exist_ok=True)
    
    # Ensure full output directory path exists
    output_dir = output_path.parent
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Save as ICO with multiple resolutions
    sizes = [16, 32, 48, 64, 128, 256]
    img.save(output_path, format="ICO", sizes=[(size, size) for size in sizes])
    
    print(f"Icon created: {output_path}")

if __name__ == "__main__":
    # Explicitly set the output path to ensure it's created in the utils folder
    create_icon("utils/icon.ico")