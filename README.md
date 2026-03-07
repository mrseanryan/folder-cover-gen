# folder-cover-gen README
Generates cover images for a tree of image folders, a bit like the folder preview feature of Dropbox.

For example:

![with-cover](./test_data/japan-by-night/has-cover/folder_cover.jpg)

![no-cover](./test_data/japan-by-night/no-cover/folder_cover.jpg)

- performance: makes use of GPU (via opencv) and multithreading

## Usage

```
./go.sh <path to root folder>
```

- note: if an image is named with the prefix `cover.` then it will always be used in the generated folder image, and be placed at the top
  - only 1 such image should appear in each folder
- if the folder already has a folder_cover.jpg file, then that folder is skipped.

## Setup

### Dependencies

1. Install uv

```
pip install uv
```

2. Install Python dependencies

```
uv python install 3.14
uv venv --python 3.14
uv sync
```

## Test

```
./test.sh
```
