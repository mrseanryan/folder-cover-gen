import cv2
import numpy as np
import random
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}

OUTPUT_NAME = "folder_cover.jpg"

COVER_SIZE = 512


# -----------------------------
# Image utilities
# -----------------------------

def load_small(path):
    """Load reduced resolution image for speed"""
    img = cv2.imread(str(path), cv2.IMREAD_REDUCED_COLOR_4)
    if img is None:
        return None
    return img


def resize_square(img, size):
    h, w = img.shape[:2]

    scale = size / max(h, w)
    new = cv2.resize(img, (int(w * scale), int(h * scale)))

    canvas = np.zeros((size, size, 3), dtype=np.uint8)

    y = (size - new.shape[0]) // 2
    x = (size - new.shape[1]) // 2

    canvas[y:y+new.shape[0], x:x+new.shape[1]] = new

    return canvas


# -----------------------------
# Rotation
# -----------------------------

def rotate_image(img, angle):
    h, w = img.shape[:2]

    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        img,
        M,
        (w, h),
        borderMode=cv2.BORDER_TRANSPARENT
    )

    return rotated


# -----------------------------
# Collage generation
# -----------------------------

def create_collage(img_paths):

    canvas = np.zeros((COVER_SIZE, COVER_SIZE, 3), dtype=np.uint8)

    imgs = []
    for p in img_paths:
        img = load_small(p)
        if img is None:
            return None

        img = resize_square(img, 320)
        imgs.append(img)

    angles = [-18, 12, -8]

    positions = [
        (80, 40),
        (150, 120),
        (40, 170)
    ]

    for img, angle, (x, y) in zip(imgs, angles, positions):

        img = rotate_image(img, angle)

        h, w = img.shape[:2]

        sub = canvas[y:y+h, x:x+w]

        mask = img.sum(axis=2) > 0

        sub[mask] = img[mask]

    return canvas


# -----------------------------
# Image selection
# -----------------------------

def get_images(folder):

    imgs = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXT]

    if len(imgs) < 3:
        return None

    return random.sample(imgs, 3)


# -----------------------------
# Folder processing
# -----------------------------

def process_folder(folder):

    out = folder / OUTPUT_NAME

    if out.exists():
        return

    imgs = get_images(folder)

    if imgs is None:
        return

    collage = create_collage(imgs)

    if collage is None:
        return

    cv2.imwrite(str(out), collage, [cv2.IMWRITE_JPEG_QUALITY, 90])


# -----------------------------
# Folder scanning
# -----------------------------

def find_photo_folders(root):

    folders = []

    for path in Path(root).rglob("*"):

        if not path.is_dir():
            continue

        images = [p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXT]

        if len(images) >= 3:
            folders.append(path)

    return folders


# -----------------------------
# Main
# -----------------------------

def main(root):

    folders = find_photo_folders(root)

    print(f"Found {len(folders)} photo folders")

    workers = os.cpu_count()

    with ProcessPoolExecutor(workers) as exe:

        list(tqdm(exe.map(process_folder, folders), total=len(folders)))


if __name__ == "__main__":

    ROOT = "/path/to/photo/library"

    main(ROOT)