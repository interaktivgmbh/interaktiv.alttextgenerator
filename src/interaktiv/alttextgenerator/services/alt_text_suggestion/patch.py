from typing import Dict
from plone.restapi.services import Service


class AltTextSuggestionPatch(Service):

    def reply(self) -> Dict:
        return {"hello": "world"}
