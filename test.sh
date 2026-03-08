#!/bin/bash
set -e

# Delete some existing covers to test that they get regenerated with the new colors:
rm ./test_data/default-colors/japan-by-night/has-cover/folder_cover.jpg | true
rm ./test_data/custom-colors/japan-by-night/has-cover/folder_cover.jpg | true

./go.sh ./test_data/default-colors --force
./go.sh ./test_data/custom-colors --force  --border_color 100,100,255 --image_padding_color 0,128,128 --canvas_background_color 150,150,255
