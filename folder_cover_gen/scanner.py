from pathlib import Path
import random

IMAGE_EXT = {".jpg",".jpeg",".png",".webp"}

def _has_folder_enough_images(folder):
    imgs=[f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXT]

    return len(imgs)>=3

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

    imgs=[p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXT]

    return imgs
