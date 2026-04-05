#!/bin/bash
set -e

uv run python -m unittest discover -s tests -v
