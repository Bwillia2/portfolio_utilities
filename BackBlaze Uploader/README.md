## Overview

- Scripts developed by Brad Williams to automatically process a local file directory of images, video, and text to be hosted on BackBlaze B2 cloud storage.

## Contents

- `backBlazeUploader.py`: Contains the logic for syncing local content with a Backblaze B2 bucket.
- `buildData.py`: Handles media processing (images and videos), reading project details from a CSV, creating a JSON output, and committing the changes to a Git repository.

## Usage

1. Ensure all environment variables mentioned in `backBlazeUploader.py` are properly set up in your system. 

2. `buildData.py` uses a variety of external libraries. Install them using:

pip install -r requirements.txt

> Note: The requirements file should contain all the necessary packages. For instance: b2sdk, PIL, moviepy, etc.

3. To run the main script:

python buildData.py


## Workflow

1. **Media Processing**: The script reads media from the `original_content` directory, processes it (resize, format change, etc.), and saves the result in `app/web_content`.

2. **CSV to JSON**: Project details are read from `projects.csv` and converted into a JSON format, which is saved as `projects.json` in `app/public/assets`.

3. **Backblaze Upload**: If `UPLOAD_TO_BACKBLAZE` is set to `True`, the processed content is synced with the specified Backblaze B2 bucket.

4. **Git Commit and Push**: The script commits the changes to the local Git repository and pushes it to the specified remote.

## Security Note

- NEVER hard-code sensitive data directly in scripts.
- Always use environment variables or other secure means to store API keys, tokens, and other sensitive details.
- It is advisable to review the scripts and understand the logic before execution, especially if working with cloud storage or version control systems.

## Contribution

Feel free to create pull requests for any enhancements or fixes. Ensure you follow secure coding practices.

## License

[MIT License](LICENSE.md)




