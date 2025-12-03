from interaktiv.alttextgenerator import _
from interaktiv.alttextgenerator.utils.generator import generate_alt_text_suggestion
from interaktiv.alttextgenerator.helper import glob_matches
from plone.registry import Registry
from plone.registry.interfaces import IRegistry
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from zope.component import getUtility
from zope.component import queryMultiAdapter


class ValidationError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


class AltTextSuggestionPatch(Service):
    def reply(self) -> Union[Dict[str, str], Any]:
        try:
            # check if generation is allowed for the current context
            self.check_generation_allowed()
            self.check_whitelisted_mimetype()
        except ValidationError as e:
            self.request.response.setStatus(e.status)
            return {"message": e.message}

        generate_alt_text_suggestion(self.context)

        serializer = queryMultiAdapter((self.context, self.request), ISerializeToJson)

        if serializer is None:
            self.request.response.setStatus(501)
            return {"message": "No serializer available."}

        serialized_content = serializer(version=self.request.get("version"))
        return serialized_content

    def check_generation_allowed(self) -> None:
        registry: Registry = getUtility(IRegistry)
        entry = "interaktiv.alttextgenerator.blacklisted_paths"
        blacklist: List[str] = registry.get(entry, [])

        if not blacklist:
            return

        content_path = "/".join(self.context.getPhysicalPath()[2:])

        if not content_path.startswith("/"):
            content_path = "/" + content_path

        if any(glob_matches(glob, content_path) for glob in blacklist):
            raise ValidationError(
                _("Alt text generation is disabled for this content."), 409
            )

    def check_whitelisted_mimetype(self) -> None:
        mimetype: str = self.context.image.contentType

        registry: Registry = getUtility(IRegistry)
        entry = "interaktiv.alttextgenerator.whitelisted_image_types"
        allowed_mimetypes: List[str] = registry.get(entry, [])

        if mimetype not in allowed_mimetypes:
            raise ValidationError(
                _("Alt text generation is not supported for this file type."), 406
            )
