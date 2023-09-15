#!/usr/bin/env python3

"""
backBlazeUploader.py

A script to sync a local folder with Backblaze storage.
"""

import os
import hashlib
from b2sdk.v1 import InMemoryAccountInfo, B2Api

# Constants
CDN_BASE_URL = os.environ.get('CDN_BASE_URL')  # Fetch from environment variable
APPLICATION_KEY = os.environ.get('B2_APPLICATION_KEY')  # Fetch from environment variable
APPLICATION_KEY_ID = os.environ.get('B2_APPLICATION_KEY_ID')  # Fetch from environment variable
BUCKET_NAME = os.environ.get('B2_BUCKET_NAME')  # Fetch from environment variable

def calculate_md5(file_path):
    """
    Calculate MD5 hash for a file.
    """
    hasher = hashlib.md5()
    with open(file_path, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()

def calculate_sha1(file_path):
    """
    Calculate SHA-1 hash for a file.
    """
    hash_sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()

def upload_file(bucket, local_path, remote_name):
    """
    Upload a file to Backblaze.
    """
    print(f"Uploading {local_path} to {remote_name}")
    bucket.upload_local_file(
        local_file=local_path,
        file_name=remote_name,
        file_infos={},
    )

def sync_with_backblaze(folder, bucket_name=BUCKET_NAME):
    """
    Sync a local folder with a Backblaze bucket.
    """
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", APPLICATION_KEY_ID, APPLICATION_KEY)
    bucket = b2_api.get_bucket_by_name(bucket_name)

    # Get list of local files and their MD5 hashes
    local_files = {}
    for root, _, files in os.walk(folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            md5_hash = calculate_md5(file_path)
            remote_file_name = file_path.replace(folder, '').lstrip(os.path.sep).replace(os.path.sep, '/')
            local_files[remote_file_name] = md5_hash

    # Fetch list of files from Backblaze
    bb_file_hashes = {}  # Maps file names to their content hash (SHA1)
    bb_file_ids = {}     # Maps file names to their file IDs

    for file_info_tuple in bucket.ls(recursive=True):
        file_info = file_info_tuple[0]  # Extract the FileVersionInfo object
        bb_file_hashes[file_info.file_name] = file_info.content_sha1
        bb_file_ids[file_info.file_name] = file_info.id_

    # Compare and sync files
    for root, _, files in os.walk(folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            remote_file_name = file_path.replace(folder, '').lstrip(os.path.sep).replace(os.path.sep, '/')
            local_file_sha1 = calculate_sha1(file_path)

            if remote_file_name in bb_file_hashes:
                # Handle modified files
                if local_file_sha1 != bb_file_hashes[remote_file_name]:
                    # First, delete the old version from Backblaze
                    try:
                        print(f"Deleting old version of {remote_file_name}")
                        bucket.delete_file_version(bb_file_ids[remote_file_name], remote_file_name)
                    except b2sdk.exception.B2Error as e:
                        print(f"Error deleting old version of {remote_file_name}: {e}")
                    
                    # Re-upload the updated file
                    upload_file(bucket, file_path, remote_file_name)
                del bb_file_hashes[remote_file_name]
                del bb_file_ids[remote_file_name]
            else:
                # Handle new files
                print (f"File doesn't exist on Backblaze, uploading {file_path} as {remote_file_name}")
                upload_file(bucket, file_path, remote_file_name)

    # Delete files from Backblaze that no longer exist locally
    for remote_file_name in bb_file_ids.keys():
        print(f"Deleting {remote_file_name} from Backblaze.")
        bucket.delete_file_version(bb_file_ids[remote_file_name], remote_file_name)

if __name__ == "__main__":
    folder_to_sync = "./path_to_folder"  # Modify this to the folder you wish to sync
    sync_with_backblaze(folder_to_sync)