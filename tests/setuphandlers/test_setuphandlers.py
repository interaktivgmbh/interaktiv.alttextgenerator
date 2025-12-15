from interaktiv.alttextgenerator.setuphandlers import alt_text_migration
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedImage
from Products.CMFPlone.tests import dummy
from unittest import mock


class TestSetuphandlers:
    @staticmethod
    def set_image_alt(image):
        image.alt_text = f"Alt text for {image.id}"
        return True

    @mock.patch(
        "interaktiv.alttextgenerator.setuphandlers.generate_alt_text_suggestion"
    )
    def test_alt_text_migration(self, mock_generate_suggestion, portal):
        # setup
        mock_generate_suggestion.side_effect = self.set_image_alt
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image1 = api.content.create(
            type="Image",
            id="test-image1",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )
        image2 = api.content.create(
            type="Image",
            id="test-image2",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )

        # do it
        alt_text_migration(None)

        # post condition
        assert image1.alt_text == "Alt text for test-image1"
        assert image2.alt_text == "Alt text for test-image2"

    @mock.patch(
        "interaktiv.alttextgenerator.setuphandlers.generate_alt_text_suggestion"
    )
    def test_alt_text_migration__not_all_empty(self, mock_generate_suggestion, portal):
        # setup
        mock_generate_suggestion.side_effect = self.set_image_alt
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image1 = api.content.create(
            type="Image",
            id="test-image1",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
            alt_text="Hello World",
        )
        image2 = api.content.create(
            type="Image",
            id="test-image2",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )

        # do it
        alt_text_migration(None)

        # post condition
        assert image1.alt_text == "Hello World"  # not modified
        assert image2.alt_text == "Alt text for test-image2"

    @mock.patch(
        "interaktiv.alttextgenerator.setuphandlers.generate_alt_text_suggestion"
    )
    def test_alt_text_migration__with_checks(self, mock_generate_suggestion, portal):
        # setup
        mock_generate_suggestion.side_effect = self.set_image_alt
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image1 = api.content.create(
            type="Image",
            id="test-image1",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )
        image2 = api.content.create(
            type="Image",
            id="test-image2",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/png", "test.png"),
        )
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.whitelisted_image_types", ["image/jpeg"]
        )
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.blacklisted_paths", ["test-image1"]
        )

        # do it
        alt_text_migration(None)

        # post condition
        assert image1.alt_text == ""  # not modified, blacklisted path
        assert image2.alt_text == ""  # not modified, image type not whitelisted
