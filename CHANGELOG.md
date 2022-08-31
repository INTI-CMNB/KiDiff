# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.1] - 2022-08-31
### Added
- Support for user defined layer names.

### Fixed
- The 'only in XXX' message worked only the first time, after caching the
  files it wasn't informed anymore.

### Changed
- Now PCB layers are cached by layer ID, not name.
- Lines in ex/include lists that begin with # are just ignored.
  Before we let them fail to match because the names weren't valid.
  This avoids confusing warnings.

## [2.4.0] - Unreleased
### Added
- Support for adding/removing SCH sheets

## [2.3.1] - 2022-08-25
### Fixed
- KiCad 5 problems with inner layers (undefined names)

## [2.3.0] - 2022-08-25
### Added
- Support for adding/removing PCB layers
- Option to specify the layers to use, instead of excluded

### Changed
- The red/green colors to match text mode diff tools

## [2.2.0] - 2022-08-24
### Added
- Multi-page schematic support.
- More control for the output name and generated files.
- Option to just populate the cache.
- Support for layer numbers in the exclude file.

### Changed
- Error codes for old/new file invalid.
  The old ones are the reserved by Python.

## [2.1.0] - 2022-08-15
### Added
- Stats diff mode
- Alternative support for Ghostscript

## [2.0.0] - 2022-08-14
### Added
- Support for schematics.

## [1.2.0] - 2022-08-13
### Added
- Support for KiCad 6.

## [1.1.0] - 2020-03-03
### Added
- Script to init the repo.

## [1.0.0] - 2020-03-03
### Added
- Initial release


