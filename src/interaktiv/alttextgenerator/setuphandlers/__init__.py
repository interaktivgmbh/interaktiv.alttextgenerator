from interaktiv.alttextgenerator import logger
from interaktiv.alttextgenerator.behaviors.alt_text_metadata import (
    IAltTextMetadataMarker,
)
from interaktiv.alttextgenerator.generator import generate_alt_text_suggestion
from interaktiv.alttexts.behaviors.alt_text import IAltTextMarker
from plone import api
from plone.app.contenttypes.content import Image
from plone.base.interfaces import INonInstallable
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from typing import List
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles:
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "interaktiv.alttextgenerator:uninstall",
        ]

    def getNonInstallableProducts(self):
        """Hide the upgrades package from site-creation and quickinstaller."""
        return [
            "interaktiv.alttextgenerator.upgrades",
        ]


def __has_empty_alt_text(obj) -> bool:
    return not (obj.alt_text and obj.alt_text.strip())


# noinspection PyUnusedLocal
def alt_text_migration(context) -> None:
    all_images = api.content.find(
        portal_type="Image",
        object_provides=(IAltTextMetadataMarker, IAltTextMarker),
        unrestricted=True,
    )

    images_filter = filter(__has_empty_alt_text, all_images)
    filtered_images: List[AbstractCatalogBrain] = list(images_filter)

    # variables for logging purpose
    total_images = len(filtered_images)
    total_migrated = 0

    for i, image in enumerate(filtered_images, start=1):
        logger.info(f"Image {i} of {total_images} queued for migration.")
        obj: Image = image.getObject()
        did_update = generate_alt_text_suggestion(obj)

        if did_update:
            total_migrated += 1

    logger.info(f"{total_migrated} of {total_images} images migrated.")
