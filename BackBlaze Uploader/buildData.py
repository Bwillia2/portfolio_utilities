import os
import csv
import json
import glob
import shutil
import hashlib
from PIL import Image
from moviepy.editor import VideoFileClip
from moviepy.video.fx import all as vfx

from backBlazeUploader import sync_with_backblaze
from git import Repo

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


class FileManager:
    def __init__(self):
        self.hashed_mirror = self.load_hashed_mirror()

    @staticmethod
    def load_hashed_mirror():
        if os.path.exists(HASHED_MIRROR_PATH):
            with open(HASHED_MIRROR_PATH, 'r') as f:
                return json.load(f)
        return {}

    @staticmethod
    def calculate_md5(file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def has_file_changed(self, source_file):
        source_md5 = self.calculate_md5(source_file)
        relative_path = os.path.relpath(source_file, IMAGE_DIR).replace(os.path.sep, '/')
        return self.hashed_mirror.get(relative_path) != source_md5

    def update_hashed_mirror(self, file_path):
        relative_path = os.path.relpath(file_path, IMAGE_DIR).replace(os.path.sep, '/')
        self.hashed_mirror[relative_path] = self.calculate_md5(file_path)

    def save_hashed_mirror(self):
        with open(HASHED_MIRROR_PATH, 'w') as f:
            json.dump(self.hashed_mirror, f)


class MediaProcessor:
    def __init__(self, file_manager):
        self.file_manager = file_manager

    @staticmethod
    def generate_absolute_url(remote_file_name):
        return os.path.join(BASE_PATH, remote_file_name).replace('\\', '/')

    def process_image(self, img_path, output_path):
        picture = Image.open(img_path)
        if "NR=" in os.path.basename(img_path):
            print(f"Skipping compression for {img_path} due to '_noresize' flag.")
        else:
            picture = picture.convert("RGB")
            picture.thumbnail(MAX_SIZE)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        picture.save(output_path, "JPEG")
        self.file_manager.update_hashed_mirror(img_path)

    def process_video(self, vid_path, clip, output_path):
        aspect_ratio = clip.size[0] / clip.size[1]
        new_height = min(MAX_VIDEO_HEIGHT, 720)
        new_width = int(aspect_ratio * new_height)

        if new_width > 1280:
            clip = clip.resize(height=new_height, width=min(new_width, 1280))
            clip = clip.fx(vfx.resize, newsize=(new_width // 2 * 2, new_height // 2 * 2))

        # Set FPS and encode the video
        clip.set_fps(18).write_videofile(
            output_path, codec='libx264', preset='ultrafast', bitrate='4000k', 
            fps=18, threads=4, ffmpeg_params=['-profile:v', 'high', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
        )
        self.file_manager.update_hashed_mirror(vid_path)

    @staticmethod
    def generate_backblaze_url(remote_file_name):
        base_url = "https://files.brad--williams.com/file/bradwilliams--assets"
        return os.path.join(base_url, remote_file_name).replace('\\', '/')

    @staticmethod
    def process_path(img_path):
        return img_path.replace(IMAGE_DIR + os.path.sep, '').replace(os.path.sep, '/').replace(' ', '_')

    @staticmethod
    def normalize_path(path):
        return path.replace('/', '\\').replace('\\', '/')

    @staticmethod
    def adjust_file_extension(url):
        base, ext = os.path.splitext(url)
        if ext in ['.gif', '.mp4']:
            return base + '.mp4'
        return url

    def process_file(self, file, item):
        remote_file_name = self.process_path(file)
        local_output_path = os.path.join(OUTPUT_DIR, remote_file_name)

        if file.endswith('.md'):
            shutil.copy2(file, local_output_path)
            url_generator = self.generate_backblaze_url if UPLOAD_TO_BACKBLAZE else self.generate_absolute_url
            item['description_path'] = url_generator(remote_file_name)
            self.file_manager.update_hashed_mirror(file)
        else:
            if any(file.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.ico', '.webp']):
                self.process_image(file, local_output_path)
            elif any(file.endswith(ext) for ext in ['.gif', '.mp4']):
                remote_file_name = os.path.splitext(remote_file_name)[0] + '.mp4'
                local_output_path_mp4 = os.path.join(OUTPUT_DIR, remote_file_name)
                self.process_video(file, VideoFileClip(file), local_output_path_mp4)

            url_generator = self.generate_backblaze_url if UPLOAD_TO_BACKBLAZE else self.generate_absolute_url
            item['images_paths'].append(url_generator(remote_file_name))


def commit_and_push():
    repo = Repo(REPO_PATH)
    repo.index.add("*")
    repo.index.commit(COMMIT_MESSAGE)
    remote = repo.remotes[REMOTE_NAME]
    remote.push(BRANCH_NAME)
    print("Changes committed and pushed.")


def process_csv_and_media():
    file_manager = FileManager()
    media_processor = MediaProcessor(file_manager)

    with open(CSV_PATH, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        projects = []
        for row in reader:
            project = {
                'id': row['ID'],
                'title': row['Title'],
                'caption': row['Caption'],
                'description_path': '',
                'images_paths': [],
                'video_path': '',
            }
            if row['File Path']:
                file_glob_path = os.path.join(IMAGE_DIR, row['File Path'])
                for file in glob.glob(file_glob_path):
                    if media_processor.normalize_path(file) not in VALID_FILE_EXTENSIONS:
                        print(f"Skipping unsupported file type: {file}")
                        continue
                    if file_manager.has_file_changed(file):
                        media_processor.process_file(file, project)

            projects.append(project)
        with open(JSON_PATH, 'w') as j:
            json.dump(projects, j, indent=4)
    file_manager.save_hashed_mirror()


if __name__ == '__main__':
    process_csv_and_media()
    if UPLOAD_TO_BACKBLAZE:
        sync_with_backblaze(OUTPUT_DIR, BUCKET_NAME)
    commit_and_push()
