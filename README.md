# folder-cover-gen README
Generates cover images for a tree of image folders, a bit like the folder preview feature of Dropbox.

Example output:

![with-cover](./test_data/default-colors/japan-by-night/has-cover/folder_cover.jpg)

The generated colors (padding, border, canvas background) can be customised:

![no-cover](./test_data/custom-colors/japan-by-night/no-cover/folder_cover.jpg)

- performance: makes use of GPU (via opencv) and multithreading

## Usage

```
./go.sh <path to root folder>
```

- note: if an image is named with the prefix `cover.` then it will always be used in the generated folder image, and be placed at the top
  - only 1 such image should appear in each folder
- if the folder already has a folder_cover.jpg file, then that folder is skipped, unless the `--force` option is used.

For more details and options, see the built-in help:

```
./go.sh
```

## Setup

### Dependencies

1. Install uv

Assumption: you have already installed a [recent version of Python](https://www.python.org/downloads/).

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

Run unit tests:

```
./test.sh
```

Run e2e tests:

```
./test.e2e.sh
```
