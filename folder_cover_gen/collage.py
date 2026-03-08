from PIL import Image, ImageOps
import cv2
import numpy as np
import random
from pathlib import Path

from . import output

COVER_SIZE = 1024
PHOTO_SIZE = 300
BORDER = 3

def load_small(path, max_dim=1200):
    output.print_debug(f"Loading image: {path}")
    try:
        img = Image.open(path)

        # ✅ Apply EXIF orientation
        img = ImageOps.exif_transpose(img)

        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        if img.mode != "RGB":
            img = img.convert("RGB")

        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Fix for transparent pixels: ensure no pixel is exactly (0,0,0)
        # because (0,0,0) is used as the transparency key during pasting.
        img[np.all(img == [0, 0, 0], axis=-1)] = [0, 0, 1]

        return img

    except Exception as e:
        output.print_error(f"Error loading image {path}: {e}")
        return None

def add_border(img):

    return cv2.copyMakeBorder(
        img,
        BORDER,
        BORDER,
        BORDER,
        BORDER,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255)
    )


def rotate(img, angle):

    h, w = img.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        img,
        M,
        (w, h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0)
    )
    
    return rotated


def add_shadow(canvas, x, y, w, h):

    shadow = canvas.copy()

    cv2.rectangle(
        shadow,
        (x+8, y+8),
        (x+w+8, y+h+8),
        (0,0,0),
        -1
    )

    alpha = 0.25

    cv2.addWeighted(shadow, alpha, canvas, 1-alpha, 0, canvas)


def expand_with_black_border(img):
    """Expand image with black background by 50%"""
    h, w = img.shape[:2]
    new_size = int(max(h, w) * 1.5)
    
    expanded = np.zeros((new_size, new_size, 3), dtype=np.uint8)
    
    y_offset = (new_size - h) // 2
    x_offset = (new_size - w) // 2
    
    expanded[y_offset:y_offset+h, x_offset:x_offset+w] = img
    
    return expanded


def paste(canvas, img, x, y):

    h, w = img.shape[:2]
    
    # Clip coordinates to canvas boundaries
    y_start = max(0, y)
    x_start = max(0, x)
    y_end = min(canvas.shape[0], y + h)
    x_end = min(canvas.shape[1], x + w)
    
    # Calculate corresponding image slice
    img_y_start = y_start - y
    img_x_start = x_start - x
    img_y_end = img_y_start + (y_end - y_start)
    img_x_end = img_x_start + (x_end - x_start)
    
    # Skip if there's nothing to paste
    if y_end <= y_start or x_end <= x_start:
        return
    
    # Get the image slice to paste
    img_slice = img[img_y_start:img_y_end, img_x_start:img_x_end]

    # Create mask - pixels where at least one channel is non-zero
    mask = np.any(img_slice != 0, axis=2)

    # Create a fresh target by reading current canvas and updating only mask pixels
    canvas[y_start:y_end, x_start:x_end][mask] = img_slice[mask]


def prepare_image(path):
    img = load_small(path)

    if img is None:
        print(f"WARNING: Failed to load image: {path}")
        return None

    img = cv2.resize(img, (PHOTO_SIZE, PHOTO_SIZE))

    img = add_border(img)
    
    img = expand_with_black_border(img)

    angle = random.uniform(-20, 20)

    img = rotate(img, angle)

    return img


def create_collage(paths):

    canvas = np.zeros((COVER_SIZE, COVER_SIZE, 3), dtype=np.uint8)

    imgs = []
    img_paths = []
    
    # First, identify the cover image by filename (case-insensitive, just the filename)
    cover_idx = None
    for i, p in enumerate(paths):
        filename = Path(p).name.lower()
        if filename.lower().startswith('cover.'):
            cover_idx = i
            break

    # Add other images first (stop at 2 if we have a cover, or 3 if we don't)
    target_count = 2 if cover_idx is not None else 3
    available_paths = [p for i, p in enumerate(paths) if i != cover_idx]
    random.shuffle(available_paths)
    
    for p in available_paths:
        img = prepare_image(p)
        if img is not None:
            imgs.append(img)
            img_paths.append(p)
        if len(imgs) >= target_count:
            break
    
    # Then prepare and add the cover image at the end (so it draws on top)
    if cover_idx is not None:
        cover_img = prepare_image(paths[cover_idx])
        if cover_img is not None:
            imgs.append(cover_img)
            img_paths.append(paths[cover_idx])
        else:
            # If cover image failed to prepare, log it
            output.print_warning(f"Cover image failed to prepare: {paths[cover_idx]}")

    if len(imgs) < 3:
        output.print_warning(f"Not enough valid images to create collage for: {paths}")
        return None

    if len(imgs) > 3:
        raise ValueError(f"Too many images prepared for collage: {len(imgs)}. Paths: {img_paths}")

    if cover_idx is not None and "cover." not in str(img_paths[-1]).lower():
        raise ValueError(f"Cover image is not at the end of the list: {img_paths[-1]}")

    positions = [
        (random.randint(80,130), random.randint(80,130)),
        (random.randint(350,400), random.randint(80,130)),
        (random.randint(215,265), random.randint(350,400))
    ]

    for img,(x,y) in zip(imgs,positions):

        h,w = img.shape[:2]

        add_shadow(canvas,x,y,w,h)
        paste(canvas,img,x,y)

    # Crop to remove excess black and add a small border
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    non_black = gray > 0
    coords = np.argwhere(non_black)
    
    if len(coords) > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # Add some padding
        padding = 20
        y_min = max(0, y_min - padding)
        x_min = max(0, x_min - padding)
        y_max = min(canvas.shape[0], y_max + padding)
        x_max = min(canvas.shape[1], x_max + padding)
        
        # Crop and ensure square aspect ratio
        crop_h = y_max - y_min
        crop_w = x_max - x_min
        crop_size = max(crop_h, crop_w)
        
        # Recenter if needed
        if crop_h < crop_size:
            y_min = max(0, y_min - (crop_size - crop_h) // 2)
            y_max = min(canvas.shape[0], y_min + crop_size)
        if crop_w < crop_size:
            x_min = max(0, x_min - (crop_size - crop_w) // 2)
            x_max = min(canvas.shape[1], x_min + crop_size)
        
        canvas = canvas[y_min:y_max, x_min:x_max]
        
        # Add black border
        border_size = 10
        canvas = cv2.copyMakeBorder(canvas, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT, value=(0, 0, 0))

    return canvas
