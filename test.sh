#!/bin/bash
set -e

rm ./test_data/japan-by-night/has-cover/folder_cover.jpg | true
# rm ./test_data/japan-by-night/no-cover/folder_cover.jpg | true

./go.sh ./test_data --force
