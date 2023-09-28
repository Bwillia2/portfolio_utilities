/* 
FigureDescriptions.jsx
This Adobe Indesign script automates the process of generating figure descriptions for images in the active document.
It does the following:
1. Gets or creates a layer named 'figure_titles' to place the figure descriptions.
2. Generates descriptions for images based on their file names.
3. Checks if the image types (link types) are valid (e.g., JPEG, PNG, TIFF).
4. Creates text frames for the descriptions and positions them below the corresponding images.
5. Applies a specified paragraph style to the descriptions.
6. Adjusts the height of the text frames to fit the content while keeping the width the same as the image frames.

Note: This script assumes that you have paragraph styles set up in your Indesign document, specifically one named "FigureDescription."
*/

var doc = app.activeDocument;

// Get or create the 'figure_titles' layer
function getOrCreateFigureTitlesLayer() {
    var figureTitlesLayer;
    try {
        figureTitlesLayer = doc.layers.itemByName('figure_titles');
        if (figureTitlesLayer.isValid) {
            // Clear all content on this layer
            while (figureTitlesLayer.pageItems.length > 0) {
                figureTitlesLayer.pageItems[0].remove();
            }
        }
    } catch (e) {
        // If layer doesn't exist, create it
        figureTitlesLayer = doc.layers.add({name: 'figure_titles'});
    }
    return figureTitlesLayer;
}

var figureTitlesLayer = getOrCreateFigureTitlesLayer();

// Generate a description from the image's file name
function generateDescription(imageName) {
    // Strip out any preceding numbers and equals sign, then remove file extension
    var description = imageName.replace(/^\d+=/, '').replace(/\.[^\.]+$/, '');
    return description;
}

// Checks to see if the link is a valid image type
function isValidImageType(link) {
    for (var i = 0; i < validImageTypes.length; i++) {
        if (link.linkType == validImageTypes[i]) {
            return true;
        }
    }
    return false;
}

// Iterate over all the images in the document
for (var i = 0; i < doc.links.length; i++) {
    var link = doc.links[i];

    var validImageTypes = ["JPEG", "PNG", "TIFF", "PDF", "WEBP", "GIF"];
    
    if (link.isValid && isValidImageType(link)) {
        var image = link.parent;
        var imageFrame = image.parent; // This is the frame/container of the image

        var description = generateDescription(link.name);
        
        var descriptionFrame = imageFrame.parentPage.textFrames.add({
            geometricBounds: [
                imageFrame.geometricBounds[2], // Top position is the bottom position of the image frame
                imageFrame.geometricBounds[1], // Left position same as the image frame
                imageFrame.geometricBounds[2] + 1, // Temporary height (will adjust later)
                imageFrame.geometricBounds[3]  // Right position same as the image frame
            ],
            contents: description,
            itemLayer: figureTitlesLayer
        });

        // Apply the paragraph style and clear overrides
        if (doc.paragraphStyles.itemByName("FigureDescription").isValid) {
            descriptionFrame.texts[0].clearOverrides();
            descriptionFrame.texts[0].appliedParagraphStyle = doc.paragraphStyles.itemByName("FigureDescription");
        }

        // Adjust the height of the text frame to fit its content, but keep the width the same as the image frame
        descriptionFrame.fit(FitOptions.FRAME_TO_CONTENT);
        descriptionFrame.geometricBounds = [
            descriptionFrame.geometricBounds[0], // Top
            imageFrame.geometricBounds[1], // Left (same as the image frame)
            descriptionFrame.geometricBounds[2], // Bottom
            imageFrame.geometricBounds[3]  // Right (same as the image frame)
        ];
    }
}
