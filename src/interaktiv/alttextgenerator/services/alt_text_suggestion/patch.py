from plone.restapi.services import Service
from typing import Dict


class AltTextSuggestionPatch(Service):
    def reply(self) -> Dict:
        return {"hello": "world"}
