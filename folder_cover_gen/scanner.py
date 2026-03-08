from pathlib import Path
import random

from . import config

IMAGE_EXT = {".jpg",".jpeg",".png",".webp"}

def _get_image_files(folder):
    return [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXT and f.name.lower() != config.OUTPUT_NAME.lower()]

def _has_folder_enough_images(folder):
    return len(_get_image_files(folder)) >= 3

def find_photo_folders(root):

    folders=[]

    for p in Path(root).rglob("*"):

        if not p.is_dir():
            continue

        if _has_folder_enough_images(p):
             folders.append(p)

    if len(folders)==0 and _has_folder_enough_images(Path(root)):
        folders.append(Path(root))

    return folders

def get_all_images_in_folder(folder):
    return _get_image_files(folder)
