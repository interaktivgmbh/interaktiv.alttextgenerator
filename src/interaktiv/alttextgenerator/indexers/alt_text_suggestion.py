from interaktiv.alttextgenerator.behaviors.alt_text_suggestion import IAltTextSuggestionMarker
from plone.indexer import indexer


@indexer(IAltTextSuggestionMarker)
def alt_text_suggestion_indexer(obj):
    return getattr(obj, "alt_text_suggestion", "")
