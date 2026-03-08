import os
from PIL import Image
import cv2
from functools import partial
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from pathlib import Path
import numpy as np
import sys
from pathlib import Path
import argparse
from . import config
from . import output
from .scanner import find_photo_folders,get_all_images_in_folder
from .collage import create_collage
from .result import Result


def safe_imwrite(path, img, quality=92):
    def _print_warning(msg):
        output.print_warning(f" - will save via PIL - {msg}")
        print(msg)

    try:
        path = Path(path)

        # Ensure folder exists
        path.parent.mkdir(parents=True, exist_ok=True)

        if img is None:
            _print_warning("imwrite fail: image is None")
            return False

        if img.size == 0:
            _print_warning("imwrite fail: empty image")
            return False

        if img.dtype != np.uint8:
            img = np.clip(img, 0, 255).astype(np.uint8)

        if np.isnan(img).any():
            _print_warning("imwrite fail: NaNs in image")
            return False

        ok = cv2.imwrite(
            str(path),
            img,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )

        if not ok:
            _print_warning(" - will save via PIL (imwrite fail: OpenCV returned False)")
            return False

        return True

    except Exception as e:
        _print_warning(f" - will save via PIL (imwrite exception: {e})")
        return False

def pillow_fallback(path, img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    Image.fromarray(img).save(path, quality=92)

def process(folder, force: bool = False):

    out=folder/config.OUTPUT_NAME

    if out.exists() and not force:
        output.print_verbose(f"[skipped] {folder} - output already exists: {out}")
        return "skipped"

    imgs=get_all_images_in_folder(folder)

    if imgs is None:
        output.print_verbose(f"[skipped] {folder} - no images found")
        return "skipped"

    collage=create_collage(imgs)

    if collage is None:
        output.print_warning(f"WARNING: Failed to create collage for folder: {folder}")
        return "skipped"

    output.print_verbose(f"Saving cover for folder: {folder} -> {out}")
    ok = safe_imwrite(out, collage)
    if not ok:
        pillow_fallback(out, collage)
    return "updated"

def main(path, force=False):
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return

    folders=find_photo_folders(path)

    if len(folders) == 0:
        print("No folders with enough images found.")
        return

    print(f"Found {len(folders)} folders to process.")

    result = Result()
    result.found_folders = len(folders)

    results = []
    if config.is_mt:
        workers=os.cpu_count()
        process_with_force = partial(process, force=force)
        with ProcessPoolExecutor(workers) as exe:
            results = list(tqdm(exe.map(process_with_force, folders), total=len(folders)))
    else:
        for folder in tqdm(folders):
            results.append(process(folder, force=force))

    result.folders_updated = results.count("updated")
    result.folders_skipped = results.count("skipped")

    print(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Photo Folder Covers — Dropbox-style folder thumbnails",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="EXAMPLES:\n"
               "    python -m folder_cover_gen.cli ~/Pictures\n"
               "    python -m folder_cover_gen.cli /Volumes/PhotoArchive --force"
    )
    parser.add_argument(
        "path",
        metavar="photo_root_folder",
        type=Path,
        help="The path to the folder which contains photo folders."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing folder_cover.jpg files."
    )

    args = parser.parse_args()
    root = args.path


    if not root.exists():
        print(f"\nError: Path does not exist: {root}\n")
        sys.exit(1)

    if not root.is_dir():
        print(f"\nError: Path is not a directory: {root}\n")
        sys.exit(1)

    main(root, force=args.force)
    print("[done]")
