# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

## 2.1.0 (2026-10-07)


### New features:

- Support for Plone 6.2. @arybakov05 
- Update to interaktiv.aiclient v3.0.0. @arybakov05 

## 2.0.2 (2026-08-24)


### Bug fixes:

- Keep the original image format after `exif_transpose` to prevent color space conversion errors. @arybakov05 [#15](https://github.com/interaktivgmbh/interaktiv.alttextgenerator/issues/15)
- Resize palette and bilevel images (GIF) in RGB space, Pillow silently ignored the resample filter for them. @arybakov05 [#15](https://github.com/interaktivgmbh/interaktiv.alttextgenerator/issues/15)
- Support HEIC, HEIF and AVIF images via `pillow-heif` and `pillow-avif-plugin`, converted to PNG. @arybakov05 [#15](https://github.com/interaktivgmbh/interaktiv.alttextgenerator/issues/15)

## 2.0.1 (2026-04-27)


### Internal:

- Pin latest version `2.0.1` of `interaktiv.aiclient`. @arybakov05

## 2.0.0 (2026-02-13)


### Breaking changes:

- Switch to implicit namespaces. @arybakov05

## 1.1.1 (2026-02-02)


### Bug fixes:

- Fix possible index mismatch during batch processing. @arybakov05
- Use session manager to maintain single connection pool during migration. @arybakov05


### Internal:

- Added more robust error handling. @arybakov05
- Normalize image orientation in b64_resized_image helper. @arybakov05

## 1.1.0 (2026-01-27)


### New features:

- Integrate batching to speed up migration. @arybakov05 [#10](https://github.com/interaktivgmbh/interaktiv.alttextgenerator/issues/10)


### Bug fixes:

- Send code 500 instead of 200 when generation fails. @arybakov05 [#10](https://github.com/interaktivgmbh/interaktiv.alttextgenerator/issues/10)

## 1.0.1 (2026-01-16)


### Bug fixes:

- Fix CMYK color space conversion error. @arybakov05 [#8](https://github.com/interaktivgmbh/interaktiv.alttextgenerator/issues/8)

## 1.0.0 (2025-12-16)


### Internal:

- Initial release. @arybakov05 [#1](https://github.com/interaktivgmbh/interaktiv.alttextgenerator/issues/1)
