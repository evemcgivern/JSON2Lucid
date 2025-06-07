#!/usr/bin/env python3
"""
GUI application for universal diagram format conversion.

This application provides a graphical interface for converting between
various diagram formats with preview and configuration options.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import threading

# Import the unified converter
from format_converter import FormatConverter


class DiagramConverterApp:
    """
    GUI application for diagram format conversion.
    
    Features:
    - Multiple input format support (JSON, GraphML)
    - Multiple output format options
    - Conversion options configuration
    - Responsive interface with progress feedback
    """
    
    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the diagram converter application.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("Diagram Format Converter")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # Set application icon if available
        try:
            icon_path = Path(__file__).parent / "utils" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))  # Convert Path to string for Tkinter
                self._log_message(f"Successfully loaded icon from: {icon_path}")
            else:
                # Add better debugging to check where we're looking
                base_dir = Path(__file__).parent
                utils_dir = base_dir / "utils"
                self._log_message(f"Icon not found at: {icon_path}")
                self._log_message(f"Base directory: {base_dir}")
                self._log_message(f"Utils directory exists: {utils_dir.exists()}")
                if utils_dir.exists():
                    self._log_message(f"Files in utils directory: {list(utils_dir.glob('*'))}")
        except Exception as e:
            # Log the specific error for debugging
            print(f"Error loading icon: {e}")
        
        # Variables for form inputs
        self.input_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.input_format_var = tk.StringVar(value="")
        self.output_format_var = tk.StringVar(value="lucidchart_csv")
        self.diagram_type_var = tk.StringVar(value="flowchart")
        self.auto_fix_var = tk.BooleanVar(value=True)
        
        # Status variables
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.is_converting = False
        
        # Create the main UI structure
        self._create_ui_layout()
        
        # Center the window
        self._center_window()
    
    def _create_ui_layout(self) -> None:
        """Create the main UI layout structure."""
        # Create main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top section for file selection
        self._create_file_section(main_container)
        
        # Middle section for format selection and options
        options_frame = ttk.LabelFrame(main_container, text="Conversion Options", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Create a 2-column layout for options
        left_options = ttk.Frame(options_frame)
        left_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_options = ttk.Frame(options_frame)
        right_options.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Add options to the columns
        self._create_format_section(left_options)
        self._create_diagram_options(right_options)
        
        # Bottom section for status and controls
        bottom_container = ttk.Frame(main_container)
        bottom_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create action buttons
        self._create_buttons_section(bottom_container)
        
        # Create status section
        self._create_status_section(bottom_container)
    
    def _create_file_section(self, parent: ttk.Frame) -> None:
        """
        Create the file selection section.
        
        Args:
            parent: Parent frame for this section
        """
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="10")
        file_frame.pack(fill=tk.X)
        
        # Input file row
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(input_frame, text="Input File:", width=12).pack(side=tk.LEFT)
        ttk.Entry(input_frame, textvariable=self.input_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(
            input_frame, 
            text="Browse...", 
            command=self._browse_input_file
        ).pack(side=tk.RIGHT)
        
        # Output file row
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(output_frame, text="Output File:", width=12).pack(side=tk.LEFT)
        ttk.Entry(output_frame, textvariable=self.output_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(
            output_frame, 
            text="Browse...", 
            command=self._browse_output_file
        ).pack(side=tk.RIGHT)
    
    def _create_format_section(self, parent: ttk.Frame) -> None:
        """
        Create the format selection section.
        
        Args:
            parent: Parent frame for this section
        """
        formats_frame = ttk.LabelFrame(parent, text="Formats", padding="10")
        formats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input format (detected automatically, read-only)
        input_fmt_frame = ttk.Frame(formats_frame)
        input_fmt_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_fmt_frame, text="Input Format:").pack(side=tk.LEFT)
        ttk.Entry(
            input_fmt_frame,
            textvariable=self.input_format_var,
            state="readonly",
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(input_fmt_frame, text="(Detected automatically)").pack(side=tk.LEFT)
        
        # Output format selection
        output_fmt_frame = ttk.Frame(formats_frame)
        output_fmt_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_fmt_frame, text="Output Format:").pack(side=tk.LEFT)
        
        # Create radio buttons for each output format
        format_labels = {
            "graphml": "GraphML",
            "lucidchart_uml": "Lucidchart UML",
            "lucidchart_csv": "Lucidchart CSV"
        }
        
        radio_frame = ttk.Frame(formats_frame)
        radio_frame.pack(fill=tk.X, pady=5)
        
        for fmt, label in format_labels.items():
            ttk.Radiobutton(
                radio_frame,
                text=label,
                value=fmt,
                variable=self.output_format_var,
                command=self._update_file_extension
            ).pack(anchor=tk.W, pady=2)
    
    def _create_diagram_options(self, parent: ttk.Frame) -> None:
        """
        Create diagram-specific options section.
        
        Args:
            parent: Parent frame for this section
        """
        diagram_frame = ttk.LabelFrame(parent, text="Diagram Options", padding="10")
        diagram_frame.pack(fill=tk.BOTH, expand=True)
        
        # Diagram type selection
        type_frame = ttk.Frame(diagram_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Diagram Type:").pack(anchor=tk.W)
        
        # Radio buttons for diagram types
        types_frame = ttk.Frame(diagram_frame)
        types_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(
            types_frame,
            text="Flowchart",
            value="flowchart",
            variable=self.diagram_type_var
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            types_frame,
            text="Sequence Diagram",
            value="sequence",
            variable=self.diagram_type_var
        ).pack(anchor=tk.W, pady=2)
        
        # Auto-fix option
        ttk.Checkbutton(
            diagram_frame,
            text="Auto-fix formatting errors",
            variable=self.auto_fix_var
        ).pack(anchor=tk.W, pady=10)
    
    def _create_buttons_section(self, parent: ttk.Frame) -> None:
        """
        Create the action buttons section.
        
        Args:
            parent: Parent frame for this section
        """
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Apply styles to the convert button
        convert_btn = ttk.Button(
            buttons_frame,
            text="Convert",
            command=self._convert_file,
            style="Accent.TButton"
        )
        convert_btn.pack(side=tk.RIGHT, padx=5)
        
        exit_btn = ttk.Button(
            buttons_frame,
            text="Exit",
            command=self.root.destroy
        )
        exit_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_status_section(self, parent: ttk.Frame) -> None:
        """
        Create the status section with log and progress indicator.
        
        Args:
            parent: Parent frame for this section
        """
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status message
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(fill=tk.X, pady=5)
        
        # Progress bar - store a reference to it
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            mode="indeterminate"
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Log text area with scrollbars
        log_frame = ttk.Frame(status_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.insert(tk.END, "Ready to convert. Select an input file to begin.\n")
        self.log_text.config(state=tk.DISABLED)
    
    def _center_window(self) -> None:
        """Center the application window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _browse_input_file(self) -> None:
        """Open file dialog to select input file."""
        filetypes = [
            ("All Supported Files", "*.json;*.graphml;*.xml"),
            ("JSON Files", "*.json"),
            ("GraphML Files", "*.graphml;*.xml"),
            ("All Files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=filetypes
        )
        
        if file_path:
            self.input_file_var.set(file_path)
            self._detect_input_format(file_path)
            self._update_file_extension()
    
    def _browse_output_file(self) -> None:
        """Open file dialog to select output file location."""
        output_format = self.output_format_var.get()
        extension = FormatConverter.OUTPUT_FORMATS.get(output_format, ".txt")
        
        filetypes = [("Output File", f"*{extension}"), ("All Files", "*.*")]
        
        file_path = filedialog.asksaveasfilename(
            title="Save Output File",
            filetypes=filetypes,
            defaultextension=extension
        )
        
        if file_path:
            self.output_file_var.set(file_path)
    
    def _detect_input_format(self, file_path: str) -> None:
        """
        Detect and update the input format based on file extension.
        
        Args:
            file_path: Path to the input file
        """
        try:
            format_name = FormatConverter.detect_format(file_path)
            self.input_format_var.set(format_name)
            
            self._log_message(f"Detected input format: {format_name}")
            
        except ValueError:
            self.input_format_var.set("unknown")
            self._log_message("Warning: Could not detect input file format")
    
    def _update_file_extension(self) -> None:
        """Update the output file path based on selected output format."""
        input_path = self.input_file_var.get()
        if not input_path:
            return
            
        # Get current output path
        current_output = self.output_file_var.get()
        
        # Only update if the output hasn't been manually specified or is empty
        if not current_output or current_output.startswith(str(Path(input_path).parent)):
            output_format = self.output_format_var.get()
            extension = FormatConverter.OUTPUT_FORMATS.get(output_format, ".txt")
            
            # Create new output path with appropriate extension
            output_path = Path(input_path).with_suffix(extension)
            self.output_file_var.set(str(output_path))
    
    def _log_message(self, message: str) -> None:
        """
        Add a message to the log text area.
        
        Args:
            message: Message to add to the log
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _update_status(self, message: str, progress: Optional[float] = None) -> None:
        """
        Update the status message and progress bar.
        
        Args:
            message: Status message to display
            progress: Progress value (0-100) or None for indeterminate
        """
        self.status_var.set(message)
        
        if progress is not None:
            self.progress_var.set(progress)
    
    def _convert_file(self) -> None:
        """Convert the selected file using the configured options."""
        if self.is_converting:
            return
            
        input_path = self.input_file_var.get()
        output_path = self.output_file_var.get() or None  # Use None for auto-naming
        
        # Validate input
        if not input_path:
            messagebox.showerror("Error", "Please select an input file.")
            return
            
        if not Path(input_path).exists():
            messagebox.showerror("Error", f"Input file not found: {input_path}")
            return
        
        # Get conversion options
        output_format = self.output_format_var.get()
        diagram_type = self.diagram_type_var.get()
        auto_fix = self.auto_fix_var.get()
        
        # Start conversion in a separate thread to keep UI responsive
        self.is_converting = True
        
        # Use the stored reference to start the progress bar
        self.progress_bar.start()
        
        self._update_status(f"Converting {Path(input_path).name}...")
        self._log_message(f"Starting conversion to {output_format}...")
        
        # Create and start conversion thread
        convert_thread = threading.Thread(
            target=self._run_conversion,
            args=(input_path, output_format, output_path, diagram_type, auto_fix)
        )
        convert_thread.daemon = True
        convert_thread.start()
    
    def _run_conversion(
        self, 
        input_path: str,
        output_format: str,
        output_path: Optional[str],
        diagram_type: str,
        auto_fix: bool
    ) -> None:
        """
        Run the conversion process in a separate thread.
        
        Args:
            input_path: Path to the input file
            output_format: Target output format
            output_path: Path for the output file or None for auto-naming
            diagram_type: Type of diagram to generate
            auto_fix: Whether to automatically fix format errors
        """
        try:
            # Perform the conversion
            result_path = FormatConverter.convert(
                input_path=input_path,
                output_format=output_format,
                output_path=output_path,
                diagram_type=diagram_type,
                auto_fix=auto_fix
            )
            
            # Update UI on success (using after to safely update from thread)
            self.root.after(0, lambda: self._conversion_completed(result_path))
            
        except Exception as e:
            # Update UI on error
            self.root.after(0, lambda: self._conversion_failed(str(e)))
    
    def _conversion_completed(self, output_path: Path) -> None:
        """
        Handle successful conversion completion.
        
        Args:
            output_path: Path to the created output file
        """
        # Stop progress bar using the stored reference
        self.progress_bar.stop()
        
        self.is_converting = False
        self._update_status(f"Conversion completed successfully!", 100)
        self._log_message(f"Created output file: {output_path}")
        
        # Show success message with instructions
        output_format = self.output_format_var.get()
        
        if output_format == "lucidchart_csv":
            instructions = (
                f"CSV file created: {output_path}\n\n"
                f"To import in Lucidchart:\n"
                f"1. Open Lucidchart\n"
                f"2. Select Import > Import from > CSV\n"
                f"3. Upload the generated CSV file"
            )
        elif output_format == "lucidchart_uml":
            instructions = (
                f"UML file created: {output_path}\n\n"
                f"To use in Lucidchart:\n"
                f"1. Open the UML file in a text editor\n"
                f"2. Copy all content\n"
                f"3. Paste into Lucidchart's editor"
            )
        else:
            instructions = f"File created: {output_path}"
            
        messagebox.showinfo("Conversion Successful", instructions)
        
        # Optionally open the file
        if messagebox.askyesno("Open File", "Would you like to open the output file?"):
            try:
                os.startfile(output_path)
            except Exception as e:
                self._log_message(f"Error opening file: {e}")

    def _conversion_failed(self, error_message: str) -> None:
        """
        Handle conversion failure.
        
        Args:
            error_message: Error message to display
        """
        # Stop progress bar using the stored reference
        self.progress_bar.stop()
        
        self.is_converting = False
        self._update_status("Conversion failed", 0)
        self._log_message(f"Error: {error_message}")
        
        messagebox.showerror("Conversion Error", f"An error occurred:\n{error_message}")


def setup_styles() -> None:
    """Set up custom styles for the application."""
    style = ttk.Style()
    
    # Use system theme if available
    try:
        if sys.platform.startswith('win'):
            style.theme_use('vista')
        elif sys.platform.startswith('darwin'):
            style.theme_use('aqua')
        else:
            style.theme_use('clam')
    except tk.TclError:
        # Fall back to default if theme not available
        pass
    
    # Configure custom button style
    style.configure('Accent.TButton', font=('', 10, 'bold'))


def main() -> int:
    """
    Main entry point for the converter GUI application.
    
    Returns:
        int: Exit code (0 for success)
    """
    root = tk.Tk()
    setup_styles()
    app = DiagramConverterApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())