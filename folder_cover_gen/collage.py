from PIL import Image, ImageOps
import cv2
import numpy as np
import random
from pathlib import Path

from . import output, config

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

        # Fix for transparent pixels: ensure no pixel is exactly TRANSPARENT_COLOR
        # because TRANSPARENT_COLOR is used as the transparency key during pasting.
        # We create a replacement color that is just slightly different from TRANSPARENT_COLOR.
        b, g, r = config.TRANSPARENT_COLOR
        # Just change blue channel by 1 to avoid exact match.
        if b < 255:
            b_rep = b + 1
        else:
            b_rep = b - 1
        REPLACEMENT_COLOR = (b_rep, g, r)

        # Now we can safely replace any pixels that were originally the transparent color with the replacement color.
        img[np.all(img == config.TRANSPARENT_COLOR, axis=-1)] = REPLACEMENT_COLOR

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
        value=config.BORDER_COLOR
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
        borderValue=config.TRANSPARENT_COLOR
    )
    
    return rotated


def add_shadow(canvas, img, x, y):
    """
    Adds a soft, blurred shadow for the given image onto the canvas.
    The shadow is shaped like the image and offset to the top-right.
    """
    shadow_offset = 8
    shadow_alpha = 0.35  # Increased alpha a bit to make the softer shadow more visible
    blur_amount = 21  # Kernel size for Gaussian Blur, must be odd

    h, w = img.shape[:2]

    # 1. Create a grayscale mask of the image's shape
    shadow_mask = (np.any(img != config.TRANSPARENT_COLOR, axis=2)).astype(np.uint8) * 255

    # 2. Blur the mask to create a soft shadow
    # The blur kernel size must be an odd number
    if blur_amount % 2 == 0:
        blur_amount += 1
    blurred_mask = cv2.GaussianBlur(shadow_mask, (blur_amount, blur_amount), 0)

    # 3. Determine the shadow's position (top-right offset)
    shadow_x_start = x + shadow_offset
    shadow_y_start = y - shadow_offset

    # 4. Calculate the region of interest (ROI) on the main canvas
    canvas_y_start = max(0, shadow_y_start)
    canvas_x_start = max(0, shadow_x_start)
    canvas_y_end = min(canvas.shape[0], shadow_y_start + h)
    canvas_x_end = min(canvas.shape[1], shadow_x_start + w)

    # If the shadow area is completely off-canvas, there's nothing to do
    if canvas_y_end <= canvas_y_start or canvas_x_end <= canvas_x_start:
        return

    # 5. Get the slice of the canvas that the shadow will be drawn on
    canvas_slice = canvas[canvas_y_start:canvas_y_end, canvas_x_start:canvas_x_end]

    # 6. Calculate the corresponding slice of the blurred mask
    mask_y_start = canvas_y_start - shadow_y_start
    mask_x_start = canvas_x_start - shadow_x_start
    mask_y_end = mask_y_start + (canvas_y_end - canvas_y_start)
    mask_x_end = mask_x_start + (canvas_x_end - canvas_x_start)
    blurred_mask_slice = blurred_mask[mask_y_start:mask_y_end, mask_x_start:mask_x_end]

    # 7. Blend the shadow onto the canvas slice
    # Normalize the mask to get alpha values (0.0 to 1.0) and scale by shadow_alpha
    # Add a new axis to allow broadcasting with the 3-channel canvas slice
    alpha_mask = (blurred_mask_slice / 255.0 * shadow_alpha)[:, :, np.newaxis]

    # The blending formula is: New = Background * (1 - alpha) + ShadowColor * alpha
    # Since ShadowColor is black (0), this simplifies to: New = Background * (1 - alpha)
    blended_slice = canvas_slice.astype(np.float32) * (1 - alpha_mask)

    # Update the canvas with the blended result
    canvas[canvas_y_start:canvas_y_end, canvas_x_start:canvas_x_end] = blended_slice.astype(np.uint8)

def expand_for_rotation(img):
    """Expand image with transparent background to make room for rotation."""
    h, w = img.shape[:2]
    new_size = int(max(h, w) * 1.5)
    
    expanded = np.full((new_size, new_size, 3), config.TRANSPARENT_COLOR, dtype=np.uint8)
    
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
    mask = np.any(img_slice != config.TRANSPARENT_COLOR, axis=2)

    # Create a fresh target by reading current canvas and updating only mask pixels
    canvas[y_start:y_end, x_start:x_end][mask] = img_slice[mask]


def prepare_image(path):
    img = load_small(path)

    if img is None:
        print(f"WARNING: Failed to load image: {path}")
        return None

    # Resize while preserving aspect ratio, and pad to square
    h, w = img.shape[:2]
    if h > w:
        new_h = PHOTO_SIZE
        new_w = int(w * (PHOTO_SIZE / h))
    else:
        new_w = PHOTO_SIZE
        new_h = int(h * (PHOTO_SIZE / w))

    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    padded = np.full((PHOTO_SIZE, PHOTO_SIZE, 3), config.IMAGE_PADDING_COLOR, dtype=np.uint8)
    y_offset = (PHOTO_SIZE - new_h) // 2
    x_offset = (PHOTO_SIZE - new_w) // 2
    padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    img = padded

    img = add_border(img)
    
    img = expand_for_rotation(img)

    angle = random.uniform(-20, 20)

    img = rotate(img, angle)

    return img


def create_collage(paths):

    canvas = np.full((COVER_SIZE, COVER_SIZE, 3), config.TRANSPARENT_COLOR, dtype=np.uint8)

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

        add_shadow(canvas,img,x,y)
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
        canvas = cv2.copyMakeBorder(canvas, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT, value=config.TRANSPARENT_COLOR)

    # Replace transparent background with the desired canvas background color
    # Note: TRANSPARENT_COLOR is (0,0,0) by default
    if config.CANVAS_BACKGROUND_COLOR != config.TRANSPARENT_COLOR:
        mask = np.all(canvas == config.TRANSPARENT_COLOR, axis=2)
        canvas[mask] = config.CANVAS_BACKGROUND_COLOR

    return canvas
