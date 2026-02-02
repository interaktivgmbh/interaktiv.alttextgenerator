# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

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
