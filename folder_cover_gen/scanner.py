from pathlib import Path
import random

IMAGE_EXT = {".jpg",".jpeg",".png",".webp"}


def find_photo_folders(root):

    folders=[]

    for p in Path(root).rglob("*"):

        if not p.is_dir():
            continue

        imgs=[f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXT]

        if len(imgs)>=3:
            folders.append(p)

    return folders


def pick_images(folder):

    imgs=[p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXT]

    if len(imgs)<3:
        return None

    return random.sample(imgs,3)
