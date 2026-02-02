from interaktiv.aiclient.types import Prompt
from interaktiv.alttextgenerator import _
from interaktiv.alttextgenerator import logger
from interaktiv.alttextgenerator.exc import ImageResizeError
from interaktiv.alttextgenerator.exc import ValidationError
from io import BytesIO
from PIL import Image as PILImage
from PIL.ImageOps import exif_transpose
from plone import api
from plone.app.contenttypes.content import Image
from plone.dexterity.content import DexterityContent
from plone.namedfile.file import NamedBlobImage
from plone.registry import Registry
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from typing import List
from typing import Optional
from typing import Tuple
from zope.component import getUtility
from zope.component.hooks import getSite

import base64
import cairosvg
import re


# see https://openrouter.ai/docs/guides/overview/multimodal/images
IMAGE_INPUT_TYPES = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
    "GIF": "image/gif",
}


def b64_resized_image(image: NamedBlobImage, size: Tuple[int, int] = (512, 512)) -> str:
    """
    Resizes the image to the given size and converts it to a base64 encoded PNG string.
    """
    image_mimetype = image.contentType

    # svgs are not supported by the OpenRouter API; therefore, they must be converted
    if image_mimetype == "image/svg+xml":
        image_bytes = cairosvg.svg2png(
            bytestring=image.data, output_width=size[0], output_height=size[1]
        )
    else:
        buffered = BytesIO()

        with PILImage.open(BytesIO(image.data)) as img:
            img = exif_transpose(img)
            img.thumbnail(size, resample=PILImage.Resampling.LANCZOS)

            img_format = img.format

            if img_format not in IMAGE_INPUT_TYPES:
                img_format = "PNG"

            image_mimetype = IMAGE_INPUT_TYPES[img_format]

            img.save(buffered, format=img_format)

        image_bytes = buffered.getvalue()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{image_mimetype};base64,{image_base64}"


def __get_prompts_from_registry(context: Image) -> Tuple[str, str]:
    registry: Registry = getUtility(IRegistry)
    system_prompt: Optional[str] = registry.get(
        "interaktiv.alttextgenerator.system_prompt"
    )
    user_prompt: str = registry.get("interaktiv.alttextgenerator.user_prompt")

    language = get_target_language(context)

    # inject target language into the user prompt
    user_prompt = user_prompt.format(language=language)

    return system_prompt, user_prompt


def construct_prompt_from_context(context: Image) -> Prompt:
    """
    Constructs a prompt from the Image context. The prompt is ready to be
    passed into the AI Client's call method. System and user prompts are
    retrieved from the registry.
    """
    result = []
    system_prompt, user_prompt = __get_prompts_from_registry(context)

    image: NamedBlobImage = context.image
    try:
        image_base64 = b64_resized_image(image)
    except Exception as e:
        raise ImageResizeError(e) from e

    if system_prompt:
        result.append({"role": "system", "content": system_prompt})

    result.append({
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": image_base64}},
        ],
    })

    return result


def get_target_language(context: DexterityContent) -> str:
    target_language = api.portal.get_current_language(context)

    # see plone.app.vocabularies.language.AvailableContentLanguageVocabulary
    site = getSite()
    ltool = getToolByName(site, "portal_languages", None)
    languages = ltool.getAvailableLanguages()

    return languages[target_language].get("native", target_language)


def glob_matches(pattern: str, path: str) -> bool:
    """Match a web path against a glob pattern."""
    if path != "/":
        path = path.lstrip("/")
        path = path.rstrip("/")

    if pattern != "/":
        pattern = pattern.lstrip("/")

    regex = re.escape(pattern)

    # ** -> zero or more segments
    regex = regex.replace(r"\*\*", ".*")
    # * -> zero or more characters inside a segment
    regex = regex.replace(r"\*", "[^/]*")
    # ? -> exactly one character
    regex = regex.replace(r"\?", ".")

    # Special case: trailing /** should match path with or without trailing slash
    if regex.endswith("/.*"):
        regex = regex[:-3] + "(/.*)?"

    regex = f"^{regex}$"
    return re.fullmatch(regex, path) is not None


def check_generation_allowed(context: Image) -> None:
    """
    Checks if generation is allowed for a given image.

    Parameters:
        context (Image): The image object.

    Raises:
        ValidationError: If the path of the image matches any blacklisted path
         patterns as defined in the Alt Text Generator Controlpanel.
    """
    registry: Registry = getUtility(IRegistry)
    entry = "interaktiv.alttextgenerator.blacklisted_paths"
    blacklist: List[str] = registry.get(entry, [])

    if not blacklist:
        return

    content_path = "/".join(context.getPhysicalPath()[2:])

    if not content_path.startswith("/"):
        content_path = "/" + content_path

    if any(glob_matches(glob, content_path) for glob in blacklist):
        raise ValidationError(
            _("Alt text generation is disabled for this content."), 409
        )


def check_whitelisted_mimetype(context: Image) -> None:
    """
    Checks if the mimetype of an image is whitelisted for further processing.

    Parameters:
        context (Image): The image object.

    Raises:
        ValidationError: If the mimetype of the image is not present in the
         whitelisted image types as defined in the Alt Text Generator
         Controlpanel.
    """
    mimetype: str = context.image.contentType

    registry: Registry = getUtility(IRegistry)
    entry = "interaktiv.alttextgenerator.whitelisted_image_types"
    allowed_mimetypes: List[str] = registry.get(entry, [])

    if mimetype not in allowed_mimetypes:
        raise ValidationError(
            _("Alt text generation is not supported for this file type."), 406
        )


def check_image_constraints(context: Image) -> bool:
    try:
        check_generation_allowed(context)
        check_whitelisted_mimetype(context)

        return True
    except ValidationError as e:
        logger.error(e)
        return False
