from datetime import datetime
from interaktiv.alttextgenerator.utils.generator import generate_alt_text_suggestion
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedImage
from Products.CMFPlone.tests import dummy
from unittest.mock import MagicMock
from unittest.mock import patch


class TestGenerator:
    @patch("interaktiv.alttextgenerator.utils.generator.getUtility")
    def test_generate_alt_text_suggestion__no_result(self, mock_get_utility, portal):
        # setup
        mock_client = MagicMock()
        mock_client.call.return_value = None
        mock_client.selected_model = "openai/gpt-4"
        mock_get_utility.return_value = mock_client

        setRoles(portal, TEST_USER_ID, ["Manager"])
        image = api.content.create(
            type="Image",
            id="test-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
            alt_text="some alt text",
        )

        # pre condition
        assert image.alt_text == "some alt text"

        # do it
        result = generate_alt_text_suggestion(image)

        # post condition
        assert result is False
        assert image.alt_text == "some alt text"  # assert unmodified
        assert image.alt_text_ai_generated is False

    @patch("interaktiv.alttextgenerator.utils.generator.getUtility")
    def test_generate_alt_text_suggestion(self, mock_get_utility, portal):
        # setup
        mock_client = MagicMock()
        mock_client.call.return_value = "Hello World!"
        mock_client.selected_model = "openai/gpt-4"
        mock_get_utility.return_value = mock_client

        setRoles(portal, TEST_USER_ID, ["Manager"])
        image = api.content.create(
            type="Image",
            id="test-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
            alt_text="some alt text",
        )

        # post condition
        assert image.alt_text == "some alt text"

        # do it
        result = generate_alt_text_suggestion(image)

        # post condition
        assert result is True
        assert image.alt_text == "Hello World!"
        assert image.alt_text_ai_generated is True
        assert image.alt_text_model_used == "openai/gpt-4"
        assert image.alt_text_generation_date == datetime.now().date()
