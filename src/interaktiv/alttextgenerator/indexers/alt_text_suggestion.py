from interaktiv.alttextgenerator.behaviors.alt_text_suggestion import (
    IAltTextSuggestionMarker,
)
from plone.indexer import indexer


@indexer(IAltTextSuggestionMarker)
def alt_text_ai_generated_indexer(obj):
    return getattr(obj, "alt_text_ai_generated", "")


@indexer(IAltTextSuggestionMarker)
def alt_text_model_used_indexer(obj):
    return getattr(obj, "alt_text_model_used", "")


@indexer(IAltTextSuggestionMarker)
def alt_text_generation_time_indexer(obj):
    return getattr(obj, "alt_text_generation_time", "")
