import unittest
from pathlib import Path

from folder_cover_gen import collage, config


class IncludeOptionTests(unittest.TestCase):
    def setUp(self):
        self.original_include_substrings = getattr(config, "INCLUDE_SUBSTRINGS", [])
        config.INCLUDE_SUBSTRINGS = []

    def tearDown(self):
        config.INCLUDE_SUBSTRINGS = self.original_include_substrings

    def test_matching_filenames_are_prioritized(self):
        config.INCLUDE_SUBSTRINGS = ["cat", "dog"]
        paths = [
            Path("zebra.jpg"),
            Path("my-cat.png"),
            Path("doggo.jpeg"),
            Path("tree.webp"),
        ]

        ordered = collage.prioritize_included_paths(paths)

        self.assertCountEqual(ordered, paths)
        self.assertIn(Path("my-cat.png"), ordered[:2])
        self.assertIn(Path("doggo.jpeg"), ordered[:2])


if __name__ == "__main__":
    unittest.main()
