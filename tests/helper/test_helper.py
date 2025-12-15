from interaktiv.alttextgenerator.exc import ValidationError
from interaktiv.alttextgenerator.helper import check_generation_allowed
from interaktiv.alttextgenerator.helper import check_whitelisted_mimetype
from interaktiv.alttextgenerator.helper import construct_prompt_from_context
from interaktiv.alttextgenerator.helper import glob_matches
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedImage
from Products.CMFPlone.tests import dummy

import pytest


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
            {"path": "/de/test", "glob": "/de/tes?", "match": True},
            {"path": "/de/test", "glob": "/de/t?st", "match": True},
            {"path": "/de/tes", "glob": "/de/tes?", "match": False},
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
            {"path": "/de/file.extension", "glob": "/de/*.*", "match": True},
            {"path": "/de/.", "glob": "/de/*.*", "match": True},
            {"path": "/de/file.extension", "glob": "/de/*:*", "match": False},
            # Recursive with file extensions
            {"path": "/a/b/c/image.png", "glob": "/a/**/*.png", "match": True},
            {"path": "/a/b/c/d/image.png", "glob": "/a/**/*.png", "match": True},
            {"path": "/a/b/c/d/image.jpg", "glob": "/a/**/*.png", "match": False},
        ]

        # do it
        for test_case in test_cases:
            matches = glob_matches(test_case["glob"], test_case["path"])
            assert matches == test_case["match"]

    def test_construct_prompt_from_context(self, portal):
        # setup
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image = api.content.create(
            type="Image",
            id="test-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.user_prompt", "User Prompt"
        )
        api.portal.set_registry_record("interaktiv.alttextgenerator.system_prompt", "")

        # do it
        prompt = construct_prompt_from_context(image)

        # post condition
        # test that the system prompt is not included if no value is set
        roles = {item["role"] for item in prompt}
        assert "user" in roles
        assert "system" not in roles

        user_item = next(item for item in prompt if item["role"] == "user")
        text_item = next(c for c in user_item["content"] if c["type"] == "text")
        assert text_item["text"] == "User Prompt"

        image_item = next(c for c in user_item["content"] if c["type"] == "image_url")
        assert image_item["image_url"]["url"].startswith("data:image/")

        # test that the system prompt is included if a value is set
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.system_prompt", "System Prompt"
        )

        prompt = construct_prompt_from_context(image)

        roles = {item["role"] for item in prompt}
        assert "user" in roles
        assert "system" in roles

        system_item = next(item for item in prompt if item["role"] == "system")
        assert system_item["content"] == "System Prompt"

        user_item = next(item for item in prompt if item["role"] == "user")
        text_item = next(c for c in user_item["content"] if c["type"] == "text")
        assert text_item["text"] == "User Prompt"

        image_item = next(c for c in user_item["content"] if c["type"] == "image_url")
        assert image_item["image_url"]["url"].startswith("data:image/")

    def test_check_generation_allowed(self, portal):
        # setup
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image = api.content.create(
            type="Image",
            id="test-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )

        # do it
        check_generation_allowed(image)

        # blacklist all items starting with "test-"
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.blacklisted_paths", ["test-*"]
        )

        with pytest.raises(ValidationError):
            check_generation_allowed(image)

    def test_check_whitelisted_mimetypes(self, portal):
        # setup
        setRoles(portal, TEST_USER_ID, ["Manager"])
        evil_image = api.content.create(
            type="Image",
            id="evil-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/evilImage", "evil-image.jpeg"),
        )
        good_image = api.content.create(
            type="Image",
            id="good-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "good-image.jpeg"),
        )

        # do it
        with pytest.raises(ValidationError):
            check_whitelisted_mimetype(evil_image)

        # this should not raise
        check_whitelisted_mimetype(good_image)
