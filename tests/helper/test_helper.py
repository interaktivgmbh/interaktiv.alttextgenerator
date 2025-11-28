from interaktiv.alttextgenerator.helper import glob_matches


class TestHelper:
    def test_glob_matches(self):
        # setup
        test_cases = [
            # Single segment *
            {"path": "/de/test", "glob": "/de/*", "match": True},
            {"path": "/de/test/test2", "glob": "/de/*", "match": False},
            {"path": "/de/", "glob": "/de/*", "match": False},
            # Recursive **
            {"path": "/de/test/test2", "glob": "/de/**", "match": True},
            {"path": "/de/test/test2/more", "glob": "/de/**", "match": True},
            {"path": "/de/test/test2/more", "glob": "/de/**/more", "match": True},
            {"path": "/de", "glob": "/de/**", "match": True},
            {"path": "/de", "glob": "/de/**/something", "match": False},
            {"path": "/de/a/b/c/d", "glob": "**/b/**", "match": True},
            # Relative patterns
            {"path": "/de/test", "glob": "*/test", "match": True},
            {"path": "/en/test", "glob": "*/test", "match": True},
            {"path": "/de/test/test2", "glob": "*/test2", "match": False},
            {"path": "/de/test/test2", "glob": "*/*/test2", "match": True},
            {"path": "/de/test/test2/more", "glob": "*/*/test2", "match": False},
            # Leading / exact match
            {"path": "/de/test", "glob": "/test", "match": False},
            {"path": "/test", "glob": "/test", "match": True},
            # Single character ?
            {"path": "/d/test", "glob": "/?/test", "match": True},
            {"path": "/de/test", "glob": "/?/test", "match": False},
            {"path": "/ab/test", "glob": "/??/test", "match": True},
            # File extensions
            {"path": "/de/test/image.png", "glob": "/de/test/*.png", "match": True},
            {"path": "/de/test/image.jpg", "glob": "/de/test/*.png", "match": False},
            {"path": "/de/test/test2/image.png", "glob": "/de/**/*.png", "match": True},
            {
                "path": "/de/test/test2/image.jpg",
                "glob": "/de/**/*.png",
                "match": False,
            },
            # Edge cases
            {"path": "/", "glob": "/", "match": True},
            {"path": "/", "glob": "*", "match": False},
            {"path": "/file", "glob": "*", "match": True},
            {"path": "/nested/file", "glob": "*/*", "match": True},
            {"path": "/nested/file/more", "glob": "*/*", "match": False},
            {"path": "/nested/file/more", "glob": "**", "match": True},
            # Mixed *
            {"path": "/a/b/c", "glob": "/a/*/c", "match": True},
            {"path": "/a/b/c/d", "glob": "/a/*/c", "match": False},
            {"path": "/a/b/c/d", "glob": "/a/*/**", "match": True},
            # Recursive with file extensions
            {"path": "/a/b/c/image.png", "glob": "/a/**/*.png", "match": True},
            {"path": "/a/b/c/d/image.png", "glob": "/a/**/*.png", "match": True},
            {"path": "/a/b/c/d/image.jpg", "glob": "/a/**/*.png", "match": False},
        ]

        # do it
        for test_case in test_cases:
            matches = glob_matches(test_case["glob"], test_case["path"])
            assert matches == test_case["match"]
