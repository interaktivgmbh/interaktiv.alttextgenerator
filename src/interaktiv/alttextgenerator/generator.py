from datetime import datetime
from interaktiv.aiclient.client import AIClient
from interaktiv.aiclient.helper import get_model_name_from_slug
from interaktiv.aiclient.interfaces import IAIClient
from interaktiv.alttextgenerator.helper import b64_resized_image
from interaktiv.alttextgenerator.helper import construct_prompt_with_image
from plone.app.contenttypes.content import Image
from plone.namedfile.file import NamedBlobImage
from zope.component import getUtility
from zope.lifecycleevent import modified


def generate_alt_text_suggestion(context: Image) -> bool:
    """Generate and update image alt text and metadata for the given context."""
    image: NamedBlobImage = context.image
    image_base64 = b64_resized_image(image)

    prompt = construct_prompt_with_image(image_base64)

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
