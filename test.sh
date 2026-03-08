#!/bin/bash
set -e

rm ./test_data/japan-by-night/has-cover/folder_cover.jpg | true
# rm ./test_data/japan-by-night/no-cover/folder_cover.jpg | true

./go.sh ./test_data --force  --border_color 100,100,255 --image_padding_color 0,128,128
