/*
ProjectText.js

This Adobe InDesign script automates the process of creating project layouts and descriptions from a CSV file and Markdown content.
It performs the following tasks:

1. Retrieves the active document or creates a new one.
2. Reads CSV data from a file named "projects.csv" located in the same directory as this script.
3. Defines a custom CSV line parsing function to handle comma-separated values correctly.
4. Retrieves project descriptions from Markdown files based on project titles.
5. Finds or creates a layer named 'scripted' to organize scripted content.
6. Iterates through CSV data and generates project layouts.
7. Clears existing scripted items on each page before creating new layouts.
8. Formats attribute names and creates a structured project description.
9. Adjusts the layout to fit content and styling.

Note: This script assumes the presence of paragraph styles named "ProjectTitle" and "LeaderDotsStyle" in your Indesign document.
*/

var doc = app.documents.length > 0 ? app.activeDocument : app.documents.add();
var csvFile = File(File($.fileName).path + "/projects.csv");

csvFile.open("r");
var csvContent = csvFile.read();
csvFile.close();

// Custom function to parse CSV lines correctly
function parseCSVLine(line) {
    var result = [];
    var inQuote = false;
    var field = "";

    for (var i = 0; i < line.length; i++) {
        var currChar = line.charAt(i);

        if (currChar === '"') {
            inQuote = !inQuote;
        } else if (currChar === ',' && !inQuote) {
            result.push(field);
            field = "";
        } else {
            field += currChar;
        }
    }
    if (field) result.push(field);

    return result;
}

function getProjectDescriptionFromMD(projectTitle) {
    // Construct the path to the .md file
    var mdFilePath = File($.fileName).path + "/original_content/" + projectTitle + "/description.md";
    
    var mdFile = File(mdFilePath);
    
    if (mdFile.exists) {
        mdFile.open("r");
        var content = mdFile.read();
        mdFile.close();
        return content;
    } else {
        // Return empty string or a placeholder if the file is not found
        return "";
    }
}

function findPageWithTitle(doc, title) {
    for (var i = 0; i < doc.pages.length; i++) {
        var page = doc.pages[i];
        var textFrames = page.textFrames.everyItem().getElements();
        for (var j = 0; j < textFrames.length; j++) {
            var frame = textFrames[j];
            if (frame.contents === title) {
                return page;
            }
        }
    }
    return null;
}

function getOrCreateScriptedLayer(doc) {
    try {
        return doc.layers.itemByName('scripted');
    } catch (e) {
        return doc.layers.add({name: 'scripted'});
    }
}

var scriptedLayer = getOrCreateScriptedLayer(doc);
var lines = csvContent.split("\n");
var headers = parseCSVLine(lines[0]);

for (var i = 1; i < lines.length; i++) {
    var currentProject = {};
    var data = parseCSVLine(lines[i]);
    
    for (var j = 0; j < headers.length; j++) {
        currentProject[headers[j]] = data[j];
    }

    createOrUpdateProjectLayout(currentProject);
}

function clearScriptedItemsOnPage(page) {
    var items = page.allPageItems;
    for (var i = items.length - 1; i >= 0; i--) { // Go backward because removal can affect the index
        if (items[i].itemLayer.name === 'scripted') {
            items[i].remove();
        }
    }
}

function createOrUpdateProjectLayout(project) {
    var page = findPageWithTitle(doc, project.title);
    
    if (page) {
        clearScriptedItemsOnPage(page);
        createProjectLayout(project, page);
    }
}

function formatAttributeName(attributeName) {
    return attributeName.replace(/_/g, ' ').replace(/\b(\w)/g, function(s) { return s.toUpperCase(); });
}

function createProjectLayout(project, page) {
    if (!page) {
        doc.pages.add();
        while (doc.pages.length <2 || doc.pages.length%2 != 1) {
            doc.pages.add();
        }
        var page = doc.pages[doc.pages.length -1];
    }
        
    var skipAttributes = ["title", "id", "locked", "page", "type"]; // Declared within the function scope
    var titleFrame = page.textFrames.add();
    titleFrame.itemLayer = scriptedLayer;
    titleFrame.geometricBounds = [0.25, 0.25, 0.75, 8.25]; // Adjust the height as needed
    titleFrame.contents = project.title;
    titleFrame.texts[0].appliedFont = app.fonts.item("Arial");
    titleFrame.texts[0].pointSize = 14; // Adjust the size as needed
    titleFrame.texts[0].appliedParagraphStyle = doc.paragraphStyles.item("ProjectTitle");

    var xPosition = 0.25;  
    var yPosition = 6;
    var contents = "";  // The content of our single text frame

    function addAttributeToLayout(attributeName, attributeValue) {
        attributeName = attributeName.charAt(0).toUpperCase() + attributeName.slice(1);
        attributeName = formatAttributeName(attributeName);
        contents += attributeName + "\t" + attributeValue + "\r";  
    }

    function isInSkipAttributes(attribute) {
        for (var i = 0; i < skipAttributes.length; i++) {
            if (attribute === skipAttributes[i]) {
                return true;
            }
        }
        return false;
    }

    function adjustFrameHeightToFitContent(frame) {
        // Check if there are lines in the text frame
        if (frame.texts[0].lines.length > 0) {
            // Get the Y value of the lower bound of the last line
            var lastLineBottom = frame.texts[0].lines[-1].baseline;
            // Adjust the text frame's geometric bounds
            frame.geometricBounds = [frame.geometricBounds[0], frame.geometricBounds[1], lastLineBottom, frame.geometricBounds[3]];
        }
    }

    for (var key in project) {
        if (!isInSkipAttributes(key) && project[key]) {
            addAttributeToLayout(key, project[key]);
        }
    }

    // Create single text frame and apply the styling
    var frame = page.textFrames.add();
    frame.itemLayer = scriptedLayer;
    frame.geometricBounds = [yPosition, xPosition, yPosition + 3, xPosition + 8];
    frame.contents = contents;
    frame.texts[0].appliedFont = app.fonts.item("Arial");
    frame.texts[0].pointSize = 9;
    frame.texts[0].appliedParagraphStyle = doc.paragraphStyles.item("LeaderDotsStyle");

    // Adjust the height of the text frame to fit its content
    adjustFrameHeightToFitContent(frame);

    //get the height of the new attribute frame
    var frameHeight = frame.geometricBounds[2] - frame.geometricBounds[0];

    // Calculate the bottom position of the frame
    var frameBottom = frame.geometricBounds[2];

    // Get the project description from the .md file
    project.description = getProjectDescriptionFromMD(project.title);

    // Create a new text frame for the project description immediately underneath `frame` (column 1)
    if (project.description) {
        // Temporarily create a single frame for the entire description
        var tempFrame = page.textFrames.add();
        tempFrame.geometricBounds = [0, xPosition, 10, xPosition + 4];  // temp size, will adjust
        tempFrame.contents = project.description;

        // Calculate total height based on the number of lines in tempFrame
        var totalLinesHeight = 0;
        if (tempFrame.lines.length > 1) {
            totalLinesHeight = tempFrame.lines[tempFrame.lines.length - 1].baseline - tempFrame.lines[0].baseline;
        } else if (tempFrame.lines.length === 1) {
            totalLinesHeight = tempFrame.lines[0].ascent + tempFrame.lines[0].descent;
        }
        tempFrame.remove();  // Remove the temporary frame

        var columnHeight = totalLinesHeight / 2 + 0.25; // add 0.25" to account for paragraph spacing
        var columnBottom = 10.5;  // 0.25" offset from the bottom of an 11" page
        var columnTop = columnBottom - columnHeight;

        // Create the first column for the description
        var descriptionFrame = page.textFrames.add();
        descriptionFrame.itemLayer = scriptedLayer;
        var colWidth = 4;
        descriptionFrame.geometricBounds = [columnTop, xPosition, columnBottom, xPosition + colWidth];
        descriptionFrame.contents = project.description;

        // Create the second column for the description
        var col2XPosition = xPosition + colWidth + 0; // 0" gap between the columns
        var descriptionFrame2 = page.textFrames.add();
        descriptionFrame2.itemLayer = scriptedLayer;
        descriptionFrame2.geometricBounds = [columnTop, col2XPosition, columnBottom, col2XPosition + colWidth];

        // Thread the text from the first to the second column
        descriptionFrame.nextTextFrame = descriptionFrame2;

        // Now adjust the positioning of the attribute frame
        var yOffset = 0.4375;  // Gap between the frames
        var frameTop = columnTop - yOffset;
        frame.geometricBounds = [frameTop - frameHeight, xPosition, frameTop, xPosition + 8];
    }
}





