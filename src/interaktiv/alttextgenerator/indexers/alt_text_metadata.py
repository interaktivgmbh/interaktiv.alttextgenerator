from interaktiv.alttextgenerator.behaviors.alt_text_metadata import (
    IAltTextMetadataMarker,
)
from plone.indexer import indexer


@indexer(IAltTextMetadataMarker)
def alt_text_ai_generated_indexer(obj):
    return getattr(obj, "alt_text_ai_generated", "")


@indexer(IAltTextMetadataMarker)
def alt_text_model_used_indexer(obj):
    return getattr(obj, "alt_text_model_used", "")


@indexer(IAltTextMetadataMarker)
def alt_text_generation_time_indexer(obj):
    return getattr(obj, "alt_text_generation_time", "")
