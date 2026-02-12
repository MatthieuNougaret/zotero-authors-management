# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-02-12
### Added
- Control pannel moved from right to left.
- UI scaling parameter to modify window size.
- UI relative coded buttons and fields positions (through the scaling parameter).

### Known Issues
- Author comparison logic needs further refinement for middle-name edge cases.
- The author’s comparison logic requires another method for more flexibility and to have a second independent comparison method.
- Author comparison optimization for large database (> 2,000 authors).
- Special characters strange behavior when unselected.


## [0.1.0] - 2026-02-11
### Added
- Initial Proof of Concept (PoC).
- Vectorized author comparison engine using NumPy.
- Pygame-based GUI for interactive filtering.
- Support for Zotero + Better BibTeX SQLite integration.
- Export functionality to CSV and JSON.

### Known Issues
- Author comparison logic needs further refinement for middle-name edge cases.
- The author’s comparison logic requires another method for more flexibility and to have a second independent comparison method.
- Author comparison speed for large database (> 5,000 authors).
- UI scaling (fixed viewed at 1200x700).
- UI hard coded buttons and fields positions.
