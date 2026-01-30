from interaktiv.alttextgenerator import logger
from interaktiv.alttextgenerator.behaviors.alt_text_metadata import (
    IAltTextMetadataMarker,
)
from interaktiv.alttextgenerator.helper import check_image_constraints
from interaktiv.alttextgenerator.utils.generator import (
    generate_alt_text_suggestion_batch,
)
from interaktiv.alttexts.behaviors.alt_text import IAltTextMarker
from plone import api
from plone.app.contenttypes.content import Image
from plone.base.interfaces import INonInstallable
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from plone.registry import Registry
from plone.registry.interfaces import IRegistry
from Products.GenericSetup.tool import SetupTool
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from typing import Callable
from typing import List
from typing import Optional
from ZODB.POSException import ConflictError
from zope.component import getUtility
from zope.interface import implementer

import transaction


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


def _has_empty_alt_texts(obj: AbstractCatalogBrain) -> bool:
    alt_text = obj.alt_text.strip() if obj.alt_text else None
    return not alt_text


def _process_batch(batch: List[Image]) -> int:
    logger.info(f"Processing {len(batch)} images.")

    try:
        updated = generate_alt_text_suggestion_batch(batch)
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing a batch: {e}")
        return 0

    if updated > 0:
        try:
            transaction.commit()
            logger.info(f"Committed changes to {updated} images.")
        except ConflictError:
            transaction.abort()
            logger.error(
                f"Failed to commit changes to {updated} images due to conflicts."
                "Aborting batch."
            )
            return 0

    return updated


# noinspection PyUnusedLocal
def alt_text_migration(
    context: Optional[SetupTool],
    filter_function: Callable[[AbstractCatalogBrain], bool] = _has_empty_alt_texts,
) -> None:
    """
    Generate alternative texts for all images implementing IAltTextBehavior
    and IAltTextMetadataBehavior. Images are additionally filtered through the
    filter_function.

    Parameters:
        context (Optional[SetupTool]): The SetupTool context. (unused)
        filter_function (Callable[[Image], bool]): A function used to filter
         images for processing. By default, this will filter by images with
         empty alt texts.

    """
    all_images = api.content.find(
        portal_type="Image",
        object_provides=(IAltTextMetadataMarker, IAltTextMarker),
        unrestricted=True,
    )

    registry: Registry = getUtility(IRegistry)
    batch_size = registry["interaktiv.alttextgenerator.batch_size"]

    batch: List[Image] = []
    total_migrated = 0

    for brain in all_images:
        if not filter_function(brain):
            continue

        obj = brain.getObject()

        if not check_image_constraints(obj):
            continue

        batch.append(obj)

        if len(batch) == batch_size:
            updated = _process_batch(batch)
            total_migrated += updated

            batch.clear()

    if batch:
        updated = _process_batch(batch)
        total_migrated += updated

    logger.info(f"{total_migrated} of total {len(all_images)} images migrated.")


# noinspection PyUnusedLocal
def post_uninstall(context: Optional[SetupTool]) -> None:
    behavior_name = "interaktiv.alttextgenerator.behavior.alt_text_metadata"
    portal_types = api.portal.get_tool("portal_types")

    for portal_type in portal_types:
        fti: DexterityFTI = portal_types.get(portal_type)

        if IDexterityFTI.providedBy(fti) and behavior_name in fti.behaviors:
            behaviors = tuple(
                behavior for behavior in fti.behaviors if behavior != behavior_name
            )
            fti.behaviors = behaviors
