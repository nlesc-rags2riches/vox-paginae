# Changelog

All notable changes to Vox Paginae are listed here. Only changes an annotator can see
go in.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-11-13

### Added

- Scans can be `.png`, `.tif` or `.tiff` files, besides `.jpg` and `.jpeg` (#90).
- How-to: annotate an item that spans two scans (#40).

### Changed

- A deed annotation file made by a newer version of the tool is never written. Its deed
  can't be opened, reopened or deleted, and the tool names the file. The other deeds
  work as usual (#68).

### Fixed

- Scans are found whatever the case of their extension, so `.JPG` files are no longer
  skipped (#161).

## [0.1.0] - 2026-11-12

First release.

[Unreleased]: https://github.com/nlesc-rags2riches/vox-paginae/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/nlesc-rags2riches/vox-paginae/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nlesc-rags2riches/vox-paginae/releases/tag/v0.1.0
