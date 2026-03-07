import os
from PIL import Image
import cv2
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from pathlib import Path
import numpy as np


from . import config
from . import output
from .scanner import find_photo_folders,get_all_images_in_folder
from .collage import create_collage
from .result import Result

OUTPUT_NAME="folder_cover.jpg"


def safe_imwrite(path, img, quality=92):
    try:
        path = Path(path)

        # Ensure folder exists
        path.parent.mkdir(parents=True, exist_ok=True)

        if img is None:
            print("imwrite fail: image is None")
            return False

        if img.size == 0:
            print("imwrite fail: empty image")
            return False

        if img.dtype != np.uint8:
            img = np.clip(img, 0, 255).astype(np.uint8)

        if np.isnan(img).any():
            print("imwrite fail: NaNs in image")
            return False

        ok = cv2.imwrite(
            str(path),
            img,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )

        if not ok:
            print("will save via PIL (imwrite fail: OpenCV returned False)")
            return False

        return True

    except Exception as e:
        print(f"will save via PIL (imwrite exception: {e})")
        return False

def pillow_fallback(path, img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    Image.fromarray(img).save(path, quality=92)

def process(folder, result: Result):

    out=folder/OUTPUT_NAME

    if out.exists():
        output.print_verbose(f"[skipped] {folder} - output already exists: {out}")
        result.folders_skipped += 1
        return

    imgs=get_all_images_in_folder(folder)

    if imgs is None:
        output.print_verbose(f"[skipped] {folder} - no images found")
        result.folders_skipped += 1
        return

    collage=create_collage(imgs)

    if collage is None:
        output.print_warning(f"WARNING: Failed to create collage for folder: {folder}")
        result.folders_skipped += 1
        return

    output.print_verbose(f"Saving cover for folder: {folder} -> {out}")
    ok = safe_imwrite(out, collage)
    if not ok:
        pillow_fallback(out, collage)
    result.folders_updated += 1

def main(path):
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return

    folders=find_photo_folders(path)

    print(f"Found {len(folders)} folders")

    result = Result()
    result.found_folders = len(folders)
    if config.is_mt:
        workers=os.cpu_count()
        with ProcessPoolExecutor(workers) as exe:
            list(tqdm(exe.map(process,folders),total=len(folders)))
    else:
        for folder in tqdm(folders):
            process(folder, result=result)

    print(result)

if __name__ == "__main__":
    import sys
    from pathlib import Path

    def print_usage():
        print("\nPhoto Folder Covers — Dropbox-style folder thumbnails\n")
        print("USAGE:")
        print("    python -m folder_cover_gen.cli <photo_root_folder>\n")
        print("ARGUMENTS:")
        print("    photo_root_folder - The path to the folder which contains photo folders>\n")
        print("EXAMPLES:")
        print("    python -m folder_cover_gen.cli ~/Pictures")
        print("    python -m folder_cover_gen.cli /Volumes/PhotoArchive\n")

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    root = Path(sys.argv[1])

    if not root.exists():
        print(f"\nError: Path does not exist: {root}\n")
        sys.exit(1)

    if not root.is_dir():
        print(f"\nError: Path is not a directory: {root}\n")
        sys.exit(1)

    main(root)
    print("[done]")
