class Result:
    found_folders = 0
    folders_updated = 0
    folders_skipped = 0

    def __init__(self):
        pass

    def __str__(self):
        return f"Result: found {self.found_folders} folders - updated {self.folders_updated}, skipped {self.folders_skipped}."
