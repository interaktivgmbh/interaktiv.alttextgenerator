from datetime import datetime
from typing import Dict, Union, Any, NoReturn, List

from interaktiv.aiclient.client import AIClient
from interaktiv.aiclient.helper import get_model_name_from_slug
from interaktiv.aiclient.interfaces import IAIClient
from interaktiv.alttextgenerator.helper import b64_resized_image, construct_prompt_with_image
from plone.namedfile.file import NamedBlobImage
from plone.registry import Registry
from plone.registry.interfaces import IRegistry
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
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

        self.update_image_alt_text()

        serializer = queryMultiAdapter((self.context, self.request), ISerializeToJson)

        if serializer is None:
            self.request.response.setStatus(501)
            return {"message": "No serializer available."}

        serialized_content = serializer(version=self.request.get("version"))
        return serialized_content

    def check_generation_enabled(self) -> Union[None, NoReturn]:
        check = True

        if not check:
            raise ValidationError("Alt text generation is disabled for this file.")

    def check_whitelisted_mimetype(self) -> Union[None, NoReturn]:
        mimetype: str = self.context.image.contentType

        registry: Registry = getUtility(IRegistry)
        allowed_mimetypes: List[str] = registry.get("interaktiv.alttextgenerator.whitelisted_image_types")

        if not mimetype in allowed_mimetypes:
            raise ValidationError("Alt text generation is not supported for this file type.")

    def update_image_alt_text(self):
        image: NamedBlobImage = self.context.image
        image_base64 = b64_resized_image(image)

        prompt = construct_prompt_with_image(image_base64)

        ai_client: AIClient = getUtility(IAIClient)
        alt_text = ai_client.call(prompt)

        selected_model = get_model_name_from_slug(ai_client.selected_model, self.context)

        self.context.alt_text_suggestion = alt_text
        self.context.alt_text_model_used = selected_model
        self.context.alt_text_generation_time = datetime.now()

        modified(self.context)
        self.context.reindexObject()
