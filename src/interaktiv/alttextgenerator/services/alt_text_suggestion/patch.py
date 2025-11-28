from datetime import datetime
from interaktiv.aiclient.client import AIClient
from interaktiv.aiclient.helper import get_model_name_from_slug
from interaktiv.aiclient.interfaces import IAIClient
from interaktiv.alttextgenerator import _
from interaktiv.alttextgenerator.helper import b64_resized_image
from interaktiv.alttextgenerator.helper import construct_prompt_with_image
from plone.namedfile.file import NamedBlobImage
from plone.registry import Registry
from plone.registry.interfaces import IRegistry
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from typing import Any
from typing import Dict
from typing import List
from typing import NoReturn
from typing import Union
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.lifecycleevent import modified


class ValidationError(Exception):
    def __init__(self, message, status=304):
        super().__init__(message)
        self.message = message
        self.status = status


class AltTextSuggestionPatch(Service):
    def reply(self) -> Union[Dict[str, str], Any]:
        try:
            # check if generation is allowed for the current context
            self.check_generation_enabled()
            self.check_whitelisted_mimetype()
        except ValidationError as e:
            self.request.response.setStatus(e.status)
            return {"message": e.message}

        self.generate_alt_text_suggestion()

        serializer = queryMultiAdapter((self.context, self.request), ISerializeToJson)

        if serializer is None:
            self.request.response.setStatus(501)
            return {"message": "No serializer available."}

        serialized_content = serializer(version=self.request.get("version"))
        return serialized_content

    def check_generation_enabled(self) -> Union[None, NoReturn]:
        # TODO add configuration for blacklisted paths and do the check
        check = True

        if not check:
            raise ValidationError(_("Alt text generation is disabled for this content."))

    def check_whitelisted_mimetype(self) -> Union[None, NoReturn]:
        mimetype: str = self.context.image.contentType

        registry: Registry = getUtility(IRegistry)
        entry = "interaktiv.alttextgenerator.whitelisted_image_types"
        allowed_mimetypes: List[str] = registry.get(entry, [])

        if not mimetype in allowed_mimetypes:
            raise ValidationError(
                _("Alt text generation is not supported for this file type.")
            )

    def generate_alt_text_suggestion(self):
        image: NamedBlobImage = self.context.image
        image_base64 = b64_resized_image(image)

        prompt = construct_prompt_with_image(image_base64)

        ai_client: AIClient = getUtility(IAIClient)
        alt_text = ai_client.call(prompt)

        selected_model = get_model_name_from_slug(
            ai_client.selected_model, self.context
        )

        self.context.alt_text = alt_text
        self.context.alt_text_ai_generated = True
        self.context.alt_text_model_used = selected_model
        self.context.alt_text_generation_time = datetime.now()

        modified(self.context)
        self.context.reindexObject()
