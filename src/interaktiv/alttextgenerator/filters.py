from plone.app.contenttypes.content import Image


def has_empty_alt_texts(obj: Image) -> bool:
    alt_text = obj.alt_text.strip() if obj.alt_text else None
    return not alt_text
