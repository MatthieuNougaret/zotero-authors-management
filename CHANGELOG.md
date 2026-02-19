# Changelog

All notable changes to this project will be documented in this file.

## [0.4.1] - 2026-02-19
### Added
- Progression bar for both database compilation and authors comparison.
- Optimize (small) Levenshtein and Damerau-Levenshtein.

## [0.4.0] - 2026-02-18
### Added
- Fix the abandonment of the use of the better-bibtex.sqlite file by the pluging. 

### Known Issues
- Author comparison logic needs further refinement for middle-name edge cases.
- Add other comparison algorithms (i.e. Jaro-Winkler, Smith–Waterman, Cosine Similarity with text embedding, K-Means...).
- Author comparison optimization for large database for distance matching (> 2,000 authors) and perfect matching (> 5,000).
- Special characters strange behavior when unselected.
- Scroll bar mouse interaction needed for faster scrolling.
- Need a progression bar for long computation phases


## [0.3.0] - 2026-02-18
### WARNING !
Your Better BibTeX data may have been migrated to a new format!

In the last Better-BibTex update, the better-bibtex.sqlite database was put into a hold to transfert all its informations into the zotero.sqlite file. This change have broked database access path of the v0.2.0.
- New current temporary status: The tool look first for better-bibtex.sqlite, if not found it look for better-bibtex.migrated and if neither of them is present will return an error indicationg that the database cannont be found.
- The risk: the ".migrated" file is a "frozen snapshot." Any papers you added or citation keys you changed after the migration will not be visible in this version of the tool.
- The fix: for the most accurate results, ensure your keys are Pinned in Zotero (Right-click -> Better BibTeX -> Pin BibTeX Key).

Full support for the new Zotero database structure is coming in v0.4.0, which will make the tool able to only use the zotero.sqlite file if the better-bibtex are not present.

### Added
- GUI controls separated into tabs for: data, settings and execution.
- Optimization (small) if abbreviation is selected and first / last name selection.
- Optimization (small) for perfect matching algorithm.
- Levenshtein and Damerau-Levenshtein comparison options.

### Known Issues
- Author comparison logic needs further refinement for middle-name edge cases.
- Add other comparison algorithms (i.e. Jaro-Winkler, Smith–Waterman, Cosine Similarity with text embedding, K-Means...).
- Author comparison optimization for large database for distance matching (> 2,000 authors) and perfect matching (> 5,000).
- Special characters strange behavior when unselected.
- Scroll bar mouse interaction needed for faster scrolling.


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
