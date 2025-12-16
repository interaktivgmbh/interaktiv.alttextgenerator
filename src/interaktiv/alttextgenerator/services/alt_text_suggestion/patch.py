from interaktiv.aiclient.client import AIClientInitializationError
from interaktiv.alttextgenerator import logger
from interaktiv.alttextgenerator.exc import ValidationError
from interaktiv.alttextgenerator.helper import check_generation_allowed
from interaktiv.alttextgenerator.helper import check_whitelisted_mimetype
from interaktiv.alttextgenerator.utils.generator import generate_alt_text_suggestion
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from typing import Any
from typing import Dict
from typing import Union
from zope.component import queryMultiAdapter


class AltTextSuggestionPatch(Service):
    def reply(self) -> Union[Dict[str, str], Any]:
        try:
            # check if generation is allowed for the current context
            check_generation_allowed(self.context)
            check_whitelisted_mimetype(self.context)
        except ValidationError as e:
            self.request.response.setStatus(e.status)
            return {"message": e.message}

        try:
            generate_alt_text_suggestion(self.context)
        except AIClientInitializationError as e:
            self.request.response.setStatus(503)
            logger.error(e)
            return {"message": "This service is currently not available."}

        serializer = queryMultiAdapter((self.context, self.request), ISerializeToJson)

        if serializer is None:
            self.request.response.setStatus(501)
            return {"message": "No serializer available."}

        serialized_content = serializer(version=self.request.get("version"))
        return serialized_content
