# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [2.5.8] - 2025-04-03
### Added
* Support for broken KiCad 9.0.1 (which changed various details in the API)
* Debug verbosity is now passed to children (#17)
* ImageMagick 7 experimental support (#19)
* Error when we can't detect a font (#19)

### Changed
* Now the git plug-in defaults to compare all the schematic pages.
  Helps to workaround bugs in KiCad 9 and IMHO is better.

## [2.5.7] - 2025-02-11
### Added
* KiCad 9 experimental support fixes (WIP)

## [2.5.6] - 2025-01-08
### Added
* KiCad 9 experimental support (WIP)

## [2.5.5] - 2024-09-12
### Added
* Workaround for KiCad 8.0.4 new feature: draw black drill marks on technical layers

## [2.5.4] - 2024-05-03
### Added
* Workaround for KiCad 8.0.2 computing hidden text when the GUI enabled it

## [2.5.3] - 2024-01-10
### Added
* New mode "2color" where you can control the added/removed colors

## [2.5.2] - 2024-01-09
### Added
* Smarter cache: changing KiCad or --zones option invalidates the cache

### Fixed
* KiRi mode for KiCad 5:
  - Plotting the worksheet makes KiCad crash, disabled

## [2.5.1] - 2024-01-03
### Added
* Option to un/fill zones


## [2.5.0] - 2023-12-20
### Added
* Support to generate KiRi SVGs *Experimental* (--kiri_mode)

### Fixed
* PNGs not removed when no diff and --only_different was specified


## [2.4.7] - 2023-03-29
### Fixed
* The message about different page size for the red_green mode

## [2.4.6] - 2023-03-29
### Fixed
- Problems when comparing two PCB/SCH with different page size using the
  red_green mode. (#5)

## [2.4.5] - 2023-03-07
### Changed
- When the bounding box of the PCB changes we make the diff using a 1:1 plot
  (not using autoscale). (#4)


## [2.4.4] - 2023-02-13
### Added
- KiCad 7 support


## [2.4.3] - 2022-10-14
### Added
- Option to skip the test for input files.
  Useful to compare from cache.
- Allow to compare two multi-page schematics even when their base name is
  different.

### Changed
- When comparing multiple sheets using the SVG mode the displayed name of the
  sheet is like the sheet path displayed by KiCad


## [2.4.2] - 2022-10-05
### Added
- Option to skip pages without diff

### Fixed
- Problems when using the plug-in and comparing uncommitted stuff.


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
