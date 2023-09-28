# Adobe Indesign Scripts 

## Overview

- Scripts developed by Brad Williams to automatically format Indesign content and sync project data with a local project database. These were developed to automatically "sync" data between my PDF portfolio and portfolio website, and keep consistent styling as things change.

## FigureDescriptions.jsx

The "FigureDescriptions.jsx" script is designed for use with Adobe Indesign. It automates the process of generating figure descriptions for images within an Indesign document. The script performs the following tasks:

- Retrieves or creates a layer named 'figure_titles' for placing figure descriptions.
- Generates descriptions for images based on their file names.
- Checks if the image types (link types) are valid (e.g., JPEG, PNG, TIFF).
- Creates text frames for the descriptions and positions them below the corresponding images.
- Applies a specified paragraph style (assumes the existence of a "FigureDescription" paragraph style).
- Adjusts the height of the text frames to fit their content while keeping the width the same as the image frames.

Please ensure that you have a paragraph style named "FigureDescription" set up in your Indesign document before running this script.

## ProjectText.js

The "ProjectText.js" script is also designed for use with Adobe Indesign. It automates the process of creating project layouts and descriptions from a CSV file and Markdown content. The script performs the following tasks:

- Retrieves the active document or creates a new one.
- Reads CSV data from a file named "projects.csv" located in the same directory as the script.
- Defines a custom CSV line parsing function to handle comma-separated values correctly.
- Retrieves project descriptions from Markdown files based on project titles.
- Finds or creates a layer named 'scripted' to organize scripted content.
- Iterates through CSV data and generates project layouts.
- Clears existing scripted items on each page before creating new layouts.
- Formats attribute names and creates a structured project description.
- Adjusts the layout to fit content and styling (assumes the existence of paragraph styles "ProjectTitle" and "LeaderDotsStyle").

Please ensure that you have the required paragraph styles ("ProjectTitle" and "LeaderDotsStyle") set up in your Indesign document before running this script.

## Usage

1. Save the script files ("FigureDescriptions.jsx" and "ProjectText.js") to a location on your computer.

2. In Adobe Indesign, open the document you want to work with or create a new one.

3. Ensure that the necessary paragraph styles ("FigureDescription," "ProjectTitle," and "LeaderDotsStyle") are defined in your Indesign document. You can customize these styles as needed.

4. Run the scripts in Adobe Indesign using the "File > Scripts > Other Script..." option and select the respective script file.

5. Follow any on-screen prompts or confirmations to execute the script. The script will automate the tasks described in its respective section.

6. Review and adjust the generated content as needed.

## Dependencies

These scripts do not have external dependencies. However, they rely on Adobe Indesign's scripting capabilities and the existence of specific paragraph styles in your Indesign document.


---

**Note**: These scripts are intended for use with Adobe Indesign and may require adjustments to suit your specific document structure and styling. Always make backups of your files before running scripts to prevent data loss.


## Contribution

Feel free to create pull requests for any enhancements or fixes. Ensure you follow secure coding practices.

## License

[MIT License](LICENSE.md)
