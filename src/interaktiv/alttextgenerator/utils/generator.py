from datetime import datetime
from interaktiv.aiclient.client import AIClient
from interaktiv.aiclient.helper import get_model_name_from_slug
from interaktiv.aiclient.interfaces import IAIClient
from interaktiv.alttextgenerator import logger
from interaktiv.alttextgenerator.exc import ImageResizeError
from interaktiv.alttextgenerator.helper import construct_prompt_from_context
from plone.app.contenttypes.content import Image
from typing import List
from zope.component import getUtility
from zope.lifecycleevent import modified


def generate_alt_text_suggestion(context: Image) -> bool:
    """Generate and update image alt text and metadata for the given context."""
    try:
        prompt = construct_prompt_from_context(context)
    except ImageResizeError as e:
        logger.error(
            f"Failed to generate alt text suggestion for image {context.id}: {e}"
        )
        return False

    ai_client: AIClient = getUtility(IAIClient)
    alt_text = ai_client.call(prompt)

    if not alt_text:
        return False

    selected_model = get_model_name_from_slug(ai_client.selected_model, context)

    context.alt_text = alt_text
    context.alt_text_ai_generated = True
    context.alt_text_model_used = selected_model
    context.alt_text_generation_date = datetime.now().date()

    modified(context)
    context.reindexObject()

    return True


def generate_alt_text_suggestion_batch(batch: List[Image]) -> int:
    """Generate and update image alt text and metadata for the given context."""
    prompts = []
    total_modified = 0

    for context in batch:
        try:
            prompt = construct_prompt_from_context(context)
            prompts.append(prompt)
        except ImageResizeError as e:
            logger.error(
                f"Failed to generate alt text suggestion for image {context.id}: {e}"
            )
            prompts.append(None)

    ai_client: AIClient = getUtility(IAIClient)
    result = ai_client.batch(prompts)

    for context, res in zip(batch, result, strict=True):
        if not res or isinstance(res, BaseException):
            continue

        selected_model = get_model_name_from_slug(ai_client.selected_model, context)

        context.alt_text = res
        context.alt_text_ai_generated = True
        context.alt_text_model_used = selected_model
        context.alt_text_generation_date = datetime.now().date()

        modified(context)
        context.reindexObject()

        total_modified += 1

    return total_modified
