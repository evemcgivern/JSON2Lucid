# JSON2Lucid

A Python application for converting JSON workflow definitions to various diagram formats including GraphML, PlantUML, and Lucidchart.

## Features

- **JSON to GraphML Conversion**: Transform JSON workflow definitions into GraphML format

- **GraphML to PlantUML**: Generate PlantUML diagrams from GraphML files

- **GraphML to Lucidchart**: Convert GraphML to Lucidchart-compatible formats

- **GUI Interface**: User-friendly graphical interface for easy conversions

- **Command Line Interface**: Batch processing and automation support

- **XML Utilities**: Robust XML processing and error correction tools

## Installation

### Using pip (recommended)

```bash

pip install json2lucid

```

### From source

1. Clone the repository

```bash

git clone https://github.com/yourusername/JSON2Lucid.git

```

2. Navigate to the project directory

```bash

cd JSON2Lucid

```

3. Install dependencies

```bash

pip install -r requirements.txt

```

4. Install the package

```bash

pip install -e .

```

## Usage

### GUI Application

Run the converter GUI for an interactive experience:

The graphical interface allows you to:

1. Select input and output files

2. Choose diagram types (sequence or flowchart)

3. Select output formats (GraphML, Lucidchart UML, or Lucidchart CSV)

4. Enable auto-fixing for common format errors

5. View conversion status and logs

## Command Line Interface - Universal Format Converter

Convert between any supported formats:

```bash

python format_converter.py input.json -f lucidchart_csv -o output.csv -t flowchart

```

Arguments:

- -f, --format: Output format (graphml, lucidchart_uml, lucidchart_csv, puml)

- -o, --output: Output file path (optional)

- -t, --type: Diagram type (sequence or flowchart)

- --no-fix: Disable automatic fixing of format errors

## GraphML to PlantUML

Convert GraphML files to PlantUML notation:

```bash

python graphml_to_plantuml.py input.graphml -o output.puml -t class

```

## GraphML to Lucidchart

Convert GraphML files to Lucidchart-compatible formats:

Arguments:

- -o, --output: Output file path

- -t, --type: Type of diagram (sequence or flowchart)

- -f, --format: Output format (uml or csv)

- --no-fix: Disable automatic fixing of GraphML XML errors

## Input File Format

JSON2Lucid expects JSON workflow files in the following format:

```json
{
  "flow": {
    "entry_condition": "Condition that starts the flow",
    "nodes": [
      {
        "id": "Node_ID",
        "entry_condition": "Condition to enter this node",
        "responsible_team": "Team responsible for this step",
        "core_responsibilities": "What happens in this step",
        "completion_criteria": "When this step is considered complete",
        "next_handoff_destinations": ["Next_Node_ID1", "Next_Node_ID2"]
      }
    ],
    "edges": [
      {
        "from": "Source_Node_ID",
        "condition": "Condition for this transition",
        "to": "Target_Node_ID"
      }
    ]
  }
}
```

## Importing to Lucidchart
After generating a Lucidchart-compatible CSV:

1. Open Lucidchart
2. Select Import > Import from > CSV
3. Upload the generated CSV file
4. Customize your diagram layout

For UML format:

1. Open the generated .uml file
2. Copy the contents
3. Paste into Lucidchart's UML editor

## Project Structure

- converter_gui.py - GUI application for format conversion

- format_converter.py - Universal converter interface

- graphml_to_plantuml.py - Converts GraphML to PlantUML notation

- graphml_to_lucidchart.py - Converts GraphML to Lucidchart formats

- json_to_graphml.py - Converts JSON workflow definitions to GraphML

- utils/ - Utility functions for XML processing and diagram generation

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add some amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request