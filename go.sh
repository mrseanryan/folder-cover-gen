#!/bin/bash
set -e

uv run python -m folder_cover_gen.cli "$@"
