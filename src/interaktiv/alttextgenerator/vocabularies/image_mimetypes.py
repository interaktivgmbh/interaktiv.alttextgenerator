from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


COMMON_IMAGE_MIMETYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/heic": ".heic",
    "image/heif": ".heif",
    "image/avif": ".avif",
}


# noInspection PyUnusedLocal
@provider(IVocabularyFactory)
def image_mimetypes_vocabulary(context) -> SimpleVocabulary:
    terms = [
        SimpleTerm(mime, mime, ext)
        for mime, ext in COMMON_IMAGE_MIMETYPE_EXTENSIONS.items()
    ]

    return SimpleVocabulary(terms)
