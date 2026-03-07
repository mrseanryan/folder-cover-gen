import os
import cv2
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

from .scanner import find_photo_folders,get_all_images_in_folder
from .collage import create_collage

OUTPUT_NAME="folder_cover.jpg"


def process(folder):

    out=folder/OUTPUT_NAME

    if out.exists():
        return

    imgs=get_all_images_in_folder(folder)

    if imgs is None:
        return

    collage=create_collage(imgs)

    if collage is None:
        return

    cv2.imwrite(str(out),collage,[cv2.IMWRITE_JPEG_QUALITY,92])


def main(path):
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return

    folders=find_photo_folders(path)

    print(f"Found {len(folders)} folders")

    is_mt = False

    if is_mt:
        workers=os.cpu_count()
        with ProcessPoolExecutor(workers) as exe:
            list(tqdm(exe.map(process,folders),total=len(folders)))
    else:
        for folder in tqdm(folders):
            process(folder)

if __name__ == "__main__":
    import sys
    from pathlib import Path

    def print_usage():
        print("\nPhoto Folder Covers — Dropbox-style folder thumbnails\n")
        print("USAGE:")
        print("    python -m foldercovers <photo_root_folder>\n")
        print("ARGUMENTS:")
        print("    photo_root_folder   Path containing photo folders\n")
        print("EXAMPLES:")
        print("    python -m foldercovers ~/Pictures")
        print("    python -m foldercovers /Volumes/PhotoArchive\n")

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
