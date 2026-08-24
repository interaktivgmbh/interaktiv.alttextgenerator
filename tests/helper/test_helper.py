from interaktiv.alttextgenerator.exc import ValidationError
from interaktiv.alttextgenerator.helper import b64_resized_image
from interaktiv.alttextgenerator.helper import check_generation_allowed
from interaktiv.alttextgenerator.helper import check_whitelisted_mimetype
from interaktiv.alttextgenerator.helper import construct_prompt_from_context
from interaktiv.alttextgenerator.helper import FORMAT_MODES
from interaktiv.alttextgenerator.helper import glob_matches
from interaktiv.alttextgenerator.helper import IMAGE_INPUT_TYPES
from interaktiv.alttextgenerator.helper import UNRESAMPLEABLE_MODES
from interaktiv.alttextgenerator.vocabularies.image_mimetypes import (
    COMMON_IMAGE_MIMETYPE_EXTENSIONS,
)
from io import BytesIO
from pathlib import Path
from PIL import Image as PILImage
from PIL import ImageChops
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedImage
from Products.CMFPlone.tests import dummy
from typing import Tuple

import base64
import math
import piexif
import pytest


ASSETS = Path(__file__).parent.parent / "assets"


def load_asset(filename: str, mimetype: str) -> NamedImage:
    data = ASSETS.joinpath(filename).read_bytes()
    return NamedImage(data, mimetype, filename)


def load_asset_rotated(
    filename: str, mimetype: str, orientation: int = 6
) -> NamedImage:
    """
    Loads a JPEG asset with an EXIF orientation tag inserted.

    Built at test time rather than checked in: this only rewrites the EXIF
    segment, not the compressed image data, so it is exactly reproducible and
    not worth the duplicated file size of a second on-disk copy.
    """
    data = ASSETS.joinpath(filename).read_bytes()
    exif = piexif.dump({"0th": {piexif.ImageIFD.Orientation: orientation}})
    rotated = BytesIO()
    piexif.insert(exif, data, rotated)
    return NamedImage(rotated.getvalue(), mimetype, filename)


def _rms(image: PILImage.Image, reference: PILImage.Image) -> float:
    """Root-mean-square pixel difference, 0 means identical."""
    difference = ImageChops.difference(
        image.convert("RGB"), reference.convert("RGB")
    ).convert("L")
    pixels = reference.size[0] * reference.size[1]
    return math.sqrt(
        sum(i * i * n for i, n in enumerate(difference.histogram())) / pixels
    )


def decode_data_url(data_url: str) -> Tuple[str, PILImage.Image]:
    header, _, payload = data_url.partition(";base64,")
    image = PILImage.open(BytesIO(base64.b64decode(payload)))
    return header[len("data:") :], image


class TestHelper:
    def test_glob_matches(self):
        # setup
        test_cases = [
            # Single segment *
            {"path": "/de/test", "glob": "/de/*", "match": True},
            {"path": "/de/test/test2", "glob": "/de/*", "match": False},
            {"path": "/de/", "glob": "/de/*", "match": False},
            # Recursive **
            {"path": "/de/test/test2", "glob": "/de/**", "match": True},
            {"path": "/de/test/test2/more", "glob": "/de/**", "match": True},
            {"path": "/de/test/test2/more", "glob": "/de/**/more", "match": True},
            {"path": "/de", "glob": "/de/**", "match": True},
            {"path": "/de", "glob": "/de/**/something", "match": False},
            {"path": "/de/a/b/c/d", "glob": "**/b/**", "match": True},
            # Relative patterns
            {"path": "/de/test", "glob": "*/test", "match": True},
            {"path": "/en/test", "glob": "*/test", "match": True},
            {"path": "/de/test/test2", "glob": "*/test2", "match": False},
            {"path": "/de/test/test2", "glob": "*/*/test2", "match": True},
            {"path": "/de/test/test2/more", "glob": "*/*/test2", "match": False},
            # Leading / exact match
            {"path": "/de/test", "glob": "/test", "match": False},
            {"path": "/test", "glob": "/test", "match": True},
            # Single character ?
            {"path": "/d/test", "glob": "/?/test", "match": True},
            {"path": "/de/test", "glob": "/?/test", "match": False},
            {"path": "/ab/test", "glob": "/??/test", "match": True},
            {"path": "/de/test", "glob": "/de/tes?", "match": True},
            {"path": "/de/test", "glob": "/de/t?st", "match": True},
            {"path": "/de/tes", "glob": "/de/tes?", "match": False},
            # File extensions
            {"path": "/de/test/image.png", "glob": "/de/test/*.png", "match": True},
            {"path": "/de/test/image.jpg", "glob": "/de/test/*.png", "match": False},
            {"path": "/de/test/test2/image.png", "glob": "/de/**/*.png", "match": True},
            {
                "path": "/de/test/test2/image.jpg",
                "glob": "/de/**/*.png",
                "match": False,
            },
            # Edge cases
            {"path": "/", "glob": "/", "match": True},
            {"path": "/", "glob": "*", "match": False},
            {"path": "/file", "glob": "*", "match": True},
            {"path": "/nested/file", "glob": "*/*", "match": True},
            {"path": "/nested/file/more", "glob": "*/*", "match": False},
            {"path": "/nested/file/more", "glob": "**", "match": True},
            # Mixed *
            {"path": "/a/b/c", "glob": "/a/*/c", "match": True},
            {"path": "/a/b/c/d", "glob": "/a/*/c", "match": False},
            {"path": "/a/b/c/d", "glob": "/a/*/**", "match": True},
            {"path": "/de/file.extension", "glob": "/de/*.*", "match": True},
            {"path": "/de/.", "glob": "/de/*.*", "match": True},
            {"path": "/de/file.extension", "glob": "/de/*:*", "match": False},
            # Recursive with file extensions
            {"path": "/a/b/c/image.png", "glob": "/a/**/*.png", "match": True},
            {"path": "/a/b/c/d/image.png", "glob": "/a/**/*.png", "match": True},
            {"path": "/a/b/c/d/image.jpg", "glob": "/a/**/*.png", "match": False},
        ]

        # do it
        for test_case in test_cases:
            matches = glob_matches(test_case["glob"], test_case["path"])
            assert matches == test_case["match"]

    def test_construct_prompt_from_context(self, portal):
        # setup
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image = api.content.create(
            type="Image",
            id="test-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.user_prompt", "User Prompt"
        )
        api.portal.set_registry_record("interaktiv.alttextgenerator.system_prompt", "")

        # do it
        prompt = construct_prompt_from_context(image)

        # post condition
        # test that the system prompt is not included if no value is set
        roles = {item["role"] for item in prompt}
        assert "user" in roles
        assert "system" not in roles

        user_item = next(item for item in prompt if item["role"] == "user")
        text_item = next(c for c in user_item["content"] if c["type"] == "text")
        assert text_item["text"] == "User Prompt"

        image_item = next(c for c in user_item["content"] if c["type"] == "image_url")
        assert image_item["image_url"]["url"].startswith("data:image/")

        # test that the system prompt is included if a value is set
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.system_prompt", "System Prompt"
        )

        prompt = construct_prompt_from_context(image)

        roles = {item["role"] for item in prompt}
        assert "user" in roles
        assert "system" in roles

        system_item = next(item for item in prompt if item["role"] == "system")
        assert system_item["content"] == "System Prompt"

        user_item = next(item for item in prompt if item["role"] == "user")
        text_item = next(c for c in user_item["content"] if c["type"] == "text")
        assert text_item["text"] == "User Prompt"

        image_item = next(c for c in user_item["content"] if c["type"] == "image_url")
        assert image_item["image_url"]["url"].startswith("data:image/")

    def test_check_generation_allowed(self, portal):
        # setup
        setRoles(portal, TEST_USER_ID, ["Manager"])
        image = api.content.create(
            type="Image",
            id="test-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "test.jpeg"),
        )

        # do it
        check_generation_allowed(image)

        # blacklist all items starting with "test-"
        api.portal.set_registry_record(
            "interaktiv.alttextgenerator.blacklisted_paths", ["test-*"]
        )

        with pytest.raises(ValidationError):
            check_generation_allowed(image)

    def test_check_whitelisted_mimetypes(self, portal):
        # setup
        setRoles(portal, TEST_USER_ID, ["Manager"])
        evil_image = api.content.create(
            type="Image",
            id="evil-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/evilImage", "evil-image.jpeg"),
        )
        good_image = api.content.create(
            type="Image",
            id="good-image",
            container=portal,
            image=NamedImage(dummy.JpegImage(), "image/jpeg", "good-image.jpeg"),
        )

        # do it
        with pytest.raises(ValidationError):
            check_whitelisted_mimetype(evil_image)

        # this should not raise
        check_whitelisted_mimetype(good_image)


class TestB64ResizedImage:
    @pytest.mark.parametrize(
        "filename,mimetype,image_format,mode",
        [
            ("rgb.jpg", "image/jpeg", "JPEG", "RGB"),
            ("cmyk.jpg", "image/jpeg", "JPEG", "CMYK"),
            ("grayscale.jpg", "image/jpeg", "JPEG", "L"),
            ("rgba.png", "image/png", "PNG", "RGBA"),
            ("palette.gif", "image/gif", "GIF", "P"),
            ("rgba.webp", "image/webp", "WEBP", "RGBA"),
        ],
    )
    def test_keeps_supported_format(
        self, filename: str, mimetype: str, image_format: str, mode: str
    ) -> None:
        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset(filename, mimetype))
        )

        # post condition
        assert result_mimetype == mimetype
        assert image.format == image_format
        assert image.mode == mode

    def test_cmyk_jpeg_is_not_converted_to_png(self) -> None:
        """A CMYK image cannot be written as PNG, converting it raises OSError."""
        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset("cmyk.jpg", "image/jpeg"))
        )

        # post condition
        assert result_mimetype == "image/jpeg"
        assert image.format == "JPEG"
        assert image.mode == "CMYK"

    @pytest.mark.parametrize(
        "filename,mimetype", [("rgb.jpg", "image/jpeg"), ("cmyk.jpg", "image/jpeg")]
    )
    def test_applies_exif_orientation(self, filename: str, mimetype: str) -> None:
        # setup
        source = PILImage.open(ASSETS / filename)
        assert source.width > source.height

        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset_rotated(filename, mimetype))
        )

        # post condition
        assert image.height > image.width
        assert result_mimetype == mimetype
        assert image.format == "JPEG"

    def test_keeps_orientation_without_exif_tag(self) -> None:
        # setup
        source = PILImage.open(ASSETS / "rgb.jpg")
        assert source.getexif().get(0x0112) is None

        # do it
        _, image = decode_data_url(
            b64_resized_image(load_asset("rgb.jpg", "image/jpeg"))
        )

        # post condition
        assert image.width > image.height

    @pytest.mark.parametrize(
        "filename,mimetype,mode",
        [("rgb.tif", "image/tiff", "RGB"), ("cmyk.tif", "image/tiff", "RGB")],
    )
    def test_converts_unsupported_format_to_png(
        self, filename: str, mimetype: str, mode: str
    ) -> None:
        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset(filename, mimetype))
        )

        # post condition
        assert result_mimetype == "image/png"
        assert image.format == "PNG"
        assert image.mode == mode

    def test_keeps_transparency(self) -> None:
        # do it
        _, image = decode_data_url(
            b64_resized_image(load_asset("rgba.png", "image/png"))
        )

        # post condition
        assert image.mode == "RGBA"
        assert min(pixel[3] for pixel in image.convert("RGBA").getdata()) == 0

    def test_converts_svg_to_png(self) -> None:
        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset("graphic.svg", "image/svg+xml"))
        )

        # post condition
        assert result_mimetype == "image/png"
        assert image.format == "PNG"

    @pytest.mark.parametrize("size", [(512, 512), (128, 128), (64, 32)])
    def test_resizes_within_bounding_box(self, size: Tuple[int, int]) -> None:
        # setup
        source = PILImage.open(ASSETS / "rgb.jpg")

        # do it
        _, image = decode_data_url(
            b64_resized_image(load_asset("rgb.jpg", "image/jpeg"), size=size)
        )

        # post condition
        assert image.width <= size[0]
        assert image.height <= size[1]
        assert image.width == pytest.approx(
            image.height * (source.width / source.height), abs=1
        )

    def test_uses_actual_data_over_declared_mimetype(self) -> None:
        """The stored contentType is not trustworthy, the image data decides."""
        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset("rgb.jpg", "image/png"))
        )

        # post condition
        assert result_mimetype == "image/jpeg"
        assert image.format == "JPEG"

    def test_raises_for_unreadable_data(self) -> None:
        # do it
        with pytest.raises(PILImage.UnidentifiedImageError):
            b64_resized_image(NamedImage(b"not an image", "image/jpeg", "broken.jpg"))

    def test_every_input_type_has_supported_modes(self) -> None:
        # post condition
        assert set(IMAGE_INPUT_TYPES) == set(FORMAT_MODES)

    @pytest.mark.parametrize("image_format", sorted(FORMAT_MODES))
    def test_format_modes_are_writable_by_pillow(self, image_format: str) -> None:
        """Guards the lookup table against drifting away from what Pillow does."""
        # do it
        for mode in FORMAT_MODES[image_format]:
            PILImage.new(mode, (8, 8)).save(BytesIO(), format=image_format)

    def test_palette_image_is_properly_resampled(self) -> None:
        """Pillow ignores the resample filter in palette mode, which aliases badly."""
        # setup
        source = PILImage.open(ASSETS / "palette.gif")
        reference = source.convert("RGB").resize(
            (512, 384), PILImage.Resampling.LANCZOS
        )
        nearest = source.resize((512, 384), PILImage.Resampling.NEAREST)

        # do it
        _, image = decode_data_url(
            b64_resized_image(load_asset("palette.gif", "image/gif"))
        )

        # post condition
        assert _rms(image, reference) < _rms(nearest, reference)

    def test_gif_keeps_transparency(self) -> None:
        # setup
        source = PILImage.open(ASSETS / "transparent.gif")
        assert "transparency" in source.info

        # do it
        _, image = decode_data_url(
            b64_resized_image(load_asset("transparent.gif", "image/gif"))
        )

        # post condition
        assert image.format == "GIF"
        assert min(pixel[3] for pixel in image.convert("RGBA").getdata()) == 0

    def test_animated_gif_is_sent_as_a_single_frame(self) -> None:
        """Vision models read one frame, animation cannot survive the request."""
        # setup
        source = PILImage.open(ASSETS / "animated.gif")
        assert source.n_frames > 1

        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset("animated.gif", "image/gif"))
        )

        # post condition
        assert result_mimetype == "image/gif"
        assert getattr(image, "n_frames", 1) == 1

    @pytest.mark.parametrize("mode", UNRESAMPLEABLE_MODES)
    def test_unresampleable_modes_ignore_the_filter(self, mode: str) -> None:
        """Guards the mode list against Pillow gaining support for them."""
        # setup
        img = PILImage.open(ASSETS / "rgb.jpg").convert(mode)

        # do it
        lanczos = img.resize((256, 192), PILImage.Resampling.LANCZOS)
        nearest = img.resize((256, 192), PILImage.Resampling.NEAREST)

        # post condition
        assert list(lanczos.getdata()) == list(nearest.getdata())

    @pytest.mark.parametrize(
        "filename,mimetype",
        [
            ("photo.heic", "image/heic"),
            ("photo.heif", "image/heif"),
            ("photo.avif", "image/avif"),
        ],
    )
    def test_converts_modern_photo_format(self, filename: str, mimetype: str) -> None:
        # do it
        result_mimetype, image = decode_data_url(
            b64_resized_image(load_asset(filename, mimetype))
        )

        # post condition
        assert result_mimetype == "image/png"
        assert image.format == "PNG"
        assert max(image.size) <= 512

    def test_modern_format_decoders_are_registered(self) -> None:
        """The pillow_avif import looks unused, removing it breaks AVIF."""
        # setup
        PILImage.init()

        # post condition
        assert "HEIF" in PILImage.OPEN
        assert "AVIF" in PILImage.OPEN

    def test_every_whitelistable_mimetype_can_be_decoded(self) -> None:
        """The control panel must not offer a format that cannot be read."""
        # setup
        PILImage.init()

        # do it
        undecodable = [
            mimetype
            for mimetype, extension in COMMON_IMAGE_MIMETYPE_EXTENSIONS.items()
            if mimetype != "image/svg+xml" and extension not in PILImage.EXTENSION
        ]

        # post condition
        assert undecodable == []
