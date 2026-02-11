# Zotero Author Duplicate Detector

Zotero is an incredible tool for managing references, but it doesn't natively handle author disambiguation.
A single accent (Benítez A. vs Benitez A.) or a middle name abbreviation (Sparks Robert Stephen John vs Robert Stephen J.) is enough to break your bibliography.

This application help to detect author duplication thorough a safe and interactive engine.


## The problem

Zotero considers the following as distinct authors:
    - Benítez M. Carmen vs Benitez M. Carmen (Accents);
    - Chollet François vs. Chollet Francois (Special characters);
    - Sparks R. S. J. vs. Sparks R. S. Jhon (Abbreviations);

This can leads to fragmented libraries and incorrect citations in research papers.


## Key Features

Some informations:
    - **Safe Database Handling:** The app never touches your original Zotero database directly. It creates a temporary copy to work on, ensuring your data remains 100% safe.
    - **Vectorized Engine:** use mainly NumPy and Pandas, allowing you to compare hundreds of authors in seconds.
    - **Special Character Toggle:** Automatically convert é, î, ö to e, i, o for matching.
    - **Abbreviation Filter:** Detect matches between full names and initials.
    - **Interactive UI:** A dedicated dashboard built with **Pygame** to filter by date (find duplicates in your imports) and visualize matches side-by-side.
    - **Export:** Generate a .csv or .json report of all detected duplicates to guide your manual cleaning in Zotero.


## Technical Stack

What was used:
    - Better BibTex Zotero plugin.
    - Language: Python 3.11.
    - UI: Pygame.
    - Data: Pandas, NumPy, SQLite3.
    - Utils: Unidecode (for accent removal), pathlib (for path).


## Getting Started

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone [https://github.com//zotero-author-detector.git](https://github.com//zotero-author-detector.git)
cd zotero-author-detector
pip install pygame pandas numpy unidecode
```

### 2. Configuration

The app needs to know where your Zotero data is.

Edit main.ini with your local paths:
```ini TOM
[PATH]
DATA_PATH = C:/Users/YourName/Zotero
SAVE_PATH = ./results
```

### 3. Running the App

```bash
python main.py
```


## How to use

List order:
    - 1. Click **(Re)Load database** to copy and index your Zotero library.
    - 2. Select your comparison criteria (**Last Name** or **First Name**).
    - 3. Toggle **Special** to ignore accents or **Abreviation** to catch name variations.
    - 4. Click **Show** to view results or **Export** to save them for later.


## Important Note

You need to have the Zotero plugin: Better BibTex and use its citation keys (define into the Zotero application).

This tool is for **detection only**!

It provides you with a list of possible duplicates so you can merge them correctly within Zotero itself if needed.


## License

MIT License
