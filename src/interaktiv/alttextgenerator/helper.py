from io import BytesIO
from PIL import Image
from plone.namedfile.file import NamedBlobImage
from plone.registry import Registry
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from zope.component import getUtility
from zope.component.hooks import getSite

import base64
import cairosvg
import re


def b64_resized_image(image: NamedBlobImage, size: Tuple[int, int] = (512, 512)) -> str:
    """Resizes the image to the given size and converts it to a base64 encoded PNG string."""
    image_mimetype = image.contentType

    # svgs are not supported by the OpenRouter API; therefore, they must be converted
    if image_mimetype == "image/svg+xml":
        image_bytes = cairosvg.svg2png(
            bytestring=image.data, output_width=size[0], output_height=size[1]
        )
    else:
        img = Image.open(BytesIO(image.data))
        img.thumbnail(size, resample=Image.Resampling.LANCZOS)

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        image_bytes = buffered.getvalue()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{image_base64}"


def construct_prompt_with_image(b64_image: str) -> List[Dict[str, Any]]:
    """
    Constructs a prompt with the given base64 encoded image.
    The prompt is ready to be passed into the AI Client's call method.
    System and user prompts are retrieved from the registry.
    """
    result = []
    registry: Registry = getUtility(IRegistry)

    system_prompt = registry.get("interaktiv.alttextgenerator.system_prompt")
    user_prompt = registry.get("interaktiv.alttextgenerator.user_prompt")

    language = get_target_language()
    user_prompt = user_prompt.format(language=language)

    if system_prompt:
        result.append({"role": "system", "content": system_prompt})

    result.append({
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": b64_image}},
        ],
    })

    return result


def get_target_language() -> str:
    registry: Registry = getUtility(IRegistry)
    target_language = registry.get("interaktiv.alttextgenerator.target_language")

    # see plone.app.vocabularies.language.AvailableContentLanguageVocabulary
    site = getSite()
    ltool = getToolByName(site, "portal_languages", None)
    languages = ltool.getAvailableLanguages()

    return languages[target_language].get("native", target_language)


def glob_matches(pattern: str, path: str) -> bool:
    """Match a web path against a glob pattern."""
    # Normalize path for relative patterns
    path_to_match = path.lstrip("/") if not pattern.startswith("/") else path
    regex = re.escape(pattern)

    # Handle wildcards
    regex = regex.replace(r"\*\*", ".*")  # ** -> zero or more segments
    regex = regex.replace(r"\*", "[^/]+")  # * -> exactly one segment
    regex = regex.replace(r"\?", ".")  # ? -> any single character

    # Special case: trailing /** should match path with or without trailing slash
    if regex.endswith("/.*"):
        regex = regex[:-3] + "(/.*)?"

    regex = f"^{regex}$"
    return re.fullmatch(regex, path_to_match) is not None
