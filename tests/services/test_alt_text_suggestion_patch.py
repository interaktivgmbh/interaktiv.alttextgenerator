from interaktiv.alttextgenerator.services.alt_text_suggestion.patch import (
    AltTextSuggestionPatch,
)
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedImage
from Products.CMFPlone.tests import dummy
from unittest import mock

import pytest


class TestAltTextSuggestionPatch:
    @pytest.fixture
    def service(self, portal, http_request):
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image = api.content.create(
            type="Image",
            id="test-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
            alt_text="some alt text",
        )

        service = AltTextSuggestionPatch()
        service.context = image
        service.request = http_request
        return service

    @mock.patch(
        "interaktiv.alttextgenerator.services.alt_text_suggestion.patch.generate_alt_text_suggestion"
    )
    def test_alt_text_suggestion_patch__checks_blacklist__included(
        self, mock_generate_suggestion, service
    ):
        # setup
        mock_generate_suggestion.return_value = None
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.blacklisted_paths", ["test-image"]
        )

        # do it
        service.reply()

        # post condition
        assert service.request.response.status == 409

    @mock.patch(
        "interaktiv.alttextgenerator.services.alt_text_suggestion.patch.generate_alt_text_suggestion"
    )
    def test_alt_text_suggestion_patch__checks_blacklist__excluded(
        self, mock_generate_suggestion, service
    ):
        # setup
        mock_generate_suggestion.return_value = True
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.blacklisted_paths", []
        )

        # do it
        service.reply()

        # post condition
        assert service.request.response.status == 200

    @mock.patch(
        "interaktiv.alttextgenerator.services.alt_text_suggestion.patch.generate_alt_text_suggestion"
    )
    def test_alt_text_suggestion_patch__checks_mimetype__included(
        self, mock_generate_suggestion, service
    ):
        # setup
        mock_generate_suggestion.return_value = True
        whitelisted_mimetypes = api.portal.get_registry_record(
            "interaktiv.alttextgenerator.whitelisted_image_types", default=[]
        )

        # pre condition
        assert "image/jpeg" in whitelisted_mimetypes

        # do it
        service.reply()

        # post condition
        assert service.request.response.status == 200

    @mock.patch(
        "interaktiv.alttextgenerator.services.alt_text_suggestion.patch.generate_alt_text_suggestion"
    )
    def test_alt_text_suggestion_patch__checks_blacklist__excluded__failed(
        self, mock_generate_suggestion, service
    ):
        # setup
        mock_generate_suggestion.return_value = False
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.blacklisted_paths", []
        )

        # do it
        service.reply()

        # post condition
        assert service.request.response.status == 500

    @mock.patch(
        "interaktiv.alttextgenerator.services.alt_text_suggestion.patch.generate_alt_text_suggestion"
    )
    def test_alt_text_suggestion_patch__checks_mimetype__included__failed(
        self, mock_generate_suggestion, service
    ):
        # setup
        mock_generate_suggestion.return_value = False
        whitelisted_mimetypes = api.portal.get_registry_record(
            "interaktiv.alttextgenerator.whitelisted_image_types", default=[]
        )

        # pre condition
        assert "image/jpeg" in whitelisted_mimetypes

        # do it
        service.reply()

        # post condition
        assert service.request.response.status == 500

    @mock.patch(
        "interaktiv.alttextgenerator.services.alt_text_suggestion.patch.generate_alt_text_suggestion"
    )
    def test_alt_text_suggestion_patch__checks_mimetype__excluded(
        self, mock_generate_suggestion, service
    ):
        # setup
        mock_generate_suggestion.return_value = None
        whitelisted_mimetypes = api.portal.get_registry_record(
            "interaktiv.alttextgenerator.whitelisted_image_types", default=[]
        )
        filtered_whitelisted_mimetypes = list(
            filter(lambda x: x != "image/jpeg", whitelisted_mimetypes)
        )
        print(filtered_whitelisted_mimetypes)
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.whitelisted_image_types",
            filtered_whitelisted_mimetypes,
        )

        # pre condition
        whitelisted_mimetypes = api.portal.get_registry_record(
            "interaktiv.alttextgenerator.whitelisted_image_types", default=[]
        )
        assert "image/jpeg" not in whitelisted_mimetypes

        # do it
        service.reply()

        # post condition
        assert service.request.response.status == 406
