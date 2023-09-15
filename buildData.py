import os
import csv
import json
import glob
import shutil
import hashlib
from PIL import Image
from moviepy.editor import VideoFileClip
from backBlazeUploader import sync_with_backblaze
from git import Repo
from moviepy.video.fx import all as vfx

# Constants
UPLOAD_TO_BACKBLAZE = True
BUCKET_NAME = 'bradwilliams--assets'
IMAGE_DIR = './original_content'
OUTPUT_DIR = './app/web_content'
CSV_PATH = './projects.csv'
JSON_PATH = './app/public/assets/projects.json'
MAX_SIZE = (1000, 1000)
MAX_VIDEO_HEIGHT = 800
REPO_PATH = "./app"
COMMIT_MESSAGE = "Automated commit"
REMOTE_NAME = "origin"
BRANCH_NAME = "main"
HASHED_MIRROR_PATH = './hashed_mirror.json'
BASE_PATH = "web_content"
VALID_FILE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.ico', '.webp', '.mp4', '.gif', '.md']

current_content = set()
hashed_mirror = {}


def load_hashed_mirror():
    """Loads the existing hashed mirror if present, or return an empty dict."""
    if os.path.exists(HASHED_MIRROR_PATH):
        with open(HASHED_MIRROR_PATH, 'r') as f:
            return json.load(f)
    return {}


def calculate_md5(file_path):
    """Calculate and return the MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()


def has_file_changed(source_file):
    """Checks if the source file content has changed by comparing MD5 hash."""
    source_md5 = calculate_md5(source_file)
    relative_path = os.path.relpath(source_file, IMAGE_DIR).replace(os.path.sep, '/')
    return hashed_mirror.get(relative_path) != source_md5


def update_hashed_mirror(file_path):
    """Update the MD5 hash of a file in the hashed mirror."""
    relative_path = os.path.relpath(file_path, IMAGE_DIR).replace(os.path.sep, '/')
    hashed_mirror[relative_path] = calculate_md5(file_path)


def save_hashed_mirror():
    """Save the hashed mirror to a JSON file."""
    with open(HASHED_MIRROR_PATH, 'w') as f:
        json.dump(hashed_mirror, f)


def generate_absolute_url(remote_file_name):
    """Generate and return the absolute URL based on the given remote file name."""
    return os.path.join(BASE_PATH, remote_file_name).replace('\\', '/')


def process_image(img_path, output_path):
    """Process, resize and save an image."""
    picture = Image.open(img_path)
    if "NR=" in os.path.basename(img_path):
        print(f"Skipping compression for {file} due to '_noresize' flag.")
    else:
        picture = picture.convert("RGB")
        picture.thumbnail(MAX_SIZE)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    picture.save(output_path, "JPEG")
    update_hashed_mirror(img_path)
    

def process_video(vid_path, clip, output_path, resize=True):
    """Process, resize and save a video."""
    aspect_ratio = clip.size[0] / clip.size[1]
    new_height = min(MAX_VIDEO_HEIGHT, 720)
    new_width = int(aspect_ratio * new_height)
    if resize or new_width > 1280:
        clip = clip.resize(height=new_height, width=min(new_width, 1280))
        clip = clip.fx(vfx.resize, newsize=(new_width // 2 * 2, new_height // 2 * 2))

    # Reduce the frame rate to 24 fps
    clip = clip.set_fps(18)

    # Use FFmpeg to encode the video with the High profile, a bitrate of 3999 kb/s, and compatible metadata
    clip.write_videofile(output_path, codec='libx264', preset='ultrafast', bitrate='4000k', fps=18, threads=4,
                     ffmpeg_params=['-profile:v', 'high', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'])
    
    update_hashed_mirror(vid_path)

def generate_backblaze_url(remote_file_name):
    """Generate and return the Backblaze URL based on the given remote file name."""
    base_url = "https://files.brad--williams.com/file/bradwilliams--assets"
    result = os.path.join(base_url, remote_file_name).replace('\\', '/')
    return result


def process_path(img_path):
    """Process a path to replace spaces with underscores and return."""
    remote_file_name = img_path.replace(IMAGE_DIR + os.path.sep, '').replace(os.path.sep, '/').replace(' ', '_')
    return remote_file_name


def commit_and_push():
    """Commit and push changes to the repository."""
    repo = Repo(REPO_PATH)
    repo.index.add("*")
    repo.index.commit(COMMIT_MESSAGE)
    remote = repo.remotes[REMOTE_NAME]
    remote.push(BRANCH_NAME)
    print("Changes committed and pushed.")

def normalize_path(path):
    """Normalize a path to use forward slashes."""
    path = path.replace('/', '\\')
    return path.replace('\\', '/')

def adjust_file_extension(url):
    """Change the file extension of a URL based on its content."""
    base, ext = os.path.splitext(url)
    if ext in ['.gif', '.mp4']:  # Add other video formats if needed.
        return base + '.mp4'
    return url

def processFile(file, item):
    """Process a file (image, video, or markdown) and update its URL in the given item."""
    remote_file_name = process_path(file)
    local_output_path = os.path.join(OUTPUT_DIR, remote_file_name)
    if file.endswith('.md'):
        shutil.copy2(file, local_output_path)
        url_generator = generate_backblaze_url if UPLOAD_TO_BACKBLAZE else generate_absolute_url
        generated_url = url_generator(remote_file_name)
        item['description_path'] = generated_url
        update_hashed_mirror(file)
    else:
        if file.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.ico', '.webp')):
            process_image(file, local_output_path)
        elif file.endswith(('.gif', '.mp4')):
            remote_file_name = os.path.splitext(remote_file_name)[0] + '.mp4'
            local_output_path_mp4 = os.path.join(OUTPUT_DIR, remote_file_name)
            clip = VideoFileClip(file)
            process_video(file, clip, local_output_path_mp4, resize=True)
        url_generator = generate_backblaze_url if UPLOAD_TO_BACKBLAZE else generate_absolute_url
        generated_url = url_generator(remote_file_name)
        item['images_paths'].append(generated_url)
    
# Sync Files in web_content
web_content_file_paths = set(glob.glob(os.path.join(OUTPUT_DIR, '**/*.*'), recursive=True))
# remove output_dir from the path to isolate the file found
web_content_files = {wc_file.replace(OUTPUT_DIR + os.path.sep, '') for wc_file in web_content_file_paths}
# replace underscores with spaces
web_content_files = {wc_file.replace('_', ' ') for wc_file in web_content_files}
# remove the file extension
web_content_files = {os.path.splitext(wc_file)[0] for wc_file in web_content_files}
#normalize the paths
web_content_files = {normalize_path(wc_file) for wc_file in web_content_files}
print(f"Found {len(web_content_files)} files in web_content")

# read the csv and convert to json
with open(CSV_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    data = list(reader)

# List of valid image extensions
valid_file_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.ico', '.webp', '.mp4', '.gif', '.md']

def get_original_files(folder, extensions):
    """Returns the list of files within a folder with the given extensions."""
    file_glob = os.path.join(folder, '**')
    return [f for f in glob.glob(file_glob, recursive=True) if os.path.isfile(f) and any(f.endswith(ext) for ext in extensions)]

def process_folder(item, web_content_files):
    """Processes an individual folder."""
    item_title_normalized = normalize_path(item['title'])
    original_folder = os.path.join(IMAGE_DIR, item_title_normalized, "PUBLIC")

    if not os.path.exists(original_folder):
        print(f"'PUBLIC' folder does not exist for the project, skipping: {original_folder}")
        return

    original_files = get_original_files(original_folder, valid_file_extensions)
    if not original_files:
        print(f"Skipping empty project folder: {original_folder}")
        return

    current_content = {normalize_path(file) for file in original_files}
    
    web_folder = normalize_path(os.path.join(OUTPUT_DIR, item['title'].replace(' ', '_').replace(os.path.sep, '/'), "PUBLIC"))
    os.makedirs(web_folder, exist_ok=True)

    item['images_paths'] = []
    for original_file_path in original_files:
        process_file(original_file_path, item, web_content_files, current_content)

def process_file(original_file_path, item, web_content_files, current_content):
    """Processes an individual file."""
    original_file_content = normalize_path(original_file_path.replace(IMAGE_DIR + os.path.sep, '')).replace(os.path.splitext(original_file_path)[1], '')
    
    if original_file_content not in current_content or has_file_changed(original_file_path):
        log_file_status(original_file_content, original_file_content in current_content)
        processFile(original_file_path, item)  # Assuming processFile adds the processed image to web_content_files
    else:
        add_to_images_paths(item, original_file_path)

def log_file_status(file_content, exists_in_web_content):
    """Logs the status of a file based on whether it exists or has changed."""
    if not exists_in_web_content:
        print(f"File does not exist: {file_content}, processing...")
    else:
        print(f"File has changed: {file_content}, overwriting...")

def add_to_images_paths(item, original_file_path):
    """Adds a URL to the images_paths of an item based on file type."""
    url_generator = generate_backblaze_url if UPLOAD_TO_BACKBLAZE else generate_absolute_url
    generated_url = url_generator(process_path(original_file_path))
    generated_url = adjust_file_extension(generated_url)
    
    if original_file_path.endswith('.md'):
        item['description_path'] = generated_url
    else:
        item['images_paths'].append(generated_url)

# Main script execution
for item in data:
    process_folder(item, web_content_files)


# Convert current_content set paths to match the format of web_content_files
current_content_names = current_content
#remove the IMAGE_DIR from the path
current_content_names = {file.replace(IMAGE_DIR + '/', '') for file in current_content_names}
#remove the file extension
current_content_names = {os.path.splitext(file)[0] for file in current_content_names}

# Find files that exist in the web content but not in the current content
orphan_files = web_content_files - current_content_names

for web_file in web_content_file_paths:
    # eliminate the output_dir from the path and its extension and underscores
    rep_file = normalize_path(web_file.replace(OUTPUT_DIR + os.path.sep, '')).replace(os.path.splitext(web_file)[1], '').replace('_', ' ')
    # normalize the path
    if rep_file in orphan_files:
        print(f"Removing orphan file: {web_file}")
        os.remove(web_file)

# Filter out the items that were skipped (i.e., ones without 'images_paths' or 'description_path')
filtered_data = [item for item in data if 'images_paths' in item and item['images_paths']]

# # write the data to the json file
with open(JSON_PATH, 'w') as jsonfile:
    json.dump(filtered_data, jsonfile, indent=2)

# Optionally upload to Backblaze
if UPLOAD_TO_BACKBLAZE:
    sync_with_backblaze(OUTPUT_DIR, BUCKET_NAME)

# commit and push to GitHub
if os.path.exists(REPO_PATH) and UPLOAD_TO_BACKBLAZE:
        commit_and_push()

save_hashed_mirror()