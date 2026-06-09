#!/usr/bin/env python3
"""
Build an inverted index of English keywords to Kalaallisut starting letters.

Reads all by-letter/*.json files, tokenizes gloss_en fields, and writes
gloss_index.json mapping each significant English keyword to the set of
Kalaallisut starting letters where that keyword appears.

Output: extracted/dictionary/gloss_index.json
Example: {"dream": ["s"], "sleep": ["s", "u"], "walk": ["a", "p"]}
"""

import json
import os
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

import nltk
from nltk.corpus import stopwords

class LazyStopwords:
    def __init__(self) -> None:
        self._stopwords: set[str] | None = None

    def _load(self) -> set[str]:
        global STOPWORDS
        if self._stopwords is None:
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                try:
                    if not nltk.download('stopwords', quiet=True):
                        raise RuntimeError("NLTK download returned False")
                except Exception as e:
                    raise RuntimeError(
                        "Failed to download NLTK 'stopwords' corpus. "
                        "Please check your internet connection, write permissions, or pre-install the corpus."
                    ) from e
            try:
                self._stopwords = set(stopwords.words('english'))
            except Exception as e:
                raise RuntimeError(
                    "NLTK 'stopwords' corpus is not available and could not be loaded. "
                    "Please check your internet connection or pre-install the corpus."
                ) from e
        STOPWORDS = self._stopwords
        return self._stopwords

    def __contains__(self, item: object) -> bool:
        return item in self._load()

STOPWORDS: set[str] = LazyStopwords()  # type: ignore

LIGATURE_TRANSLATION = str.maketrans({
    "æ": "ae",
    "ø": "o",
    "å": "a",
    "œ": "oe"
})

def tokenize_gloss(gloss: str) -> set[str]:
    # Strip contractions/possessives before splitting to avoid false matches
    # ("don't" → "do", "person's" → "person"), then extract only alpha tokens.
    text = gloss.lower()
    text = re.sub(r"n['’]t\b", "", text)
    text = re.sub(r"['’]s\b", "", text)
    # Replace common ligatures/special characters to avoid losing them or corrupting words
    text = text.translate(LIGATURE_TRANSLATION)
    # Normalize unicode characters to strip diacritics (e.g., cliché -> cliche)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    tokens = re.findall(r'\b[a-z]{3,}\b', text)
    return {t for t in tokens if t not in STOPWORDS}

def build_gloss_index(by_letter_dir: Path, output_file: Path) -> None:
    """
    Build the gloss index from all by-letter JSON files.
    """
    index = defaultdict(set)

    by_letter_dir = Path(by_letter_dir)
    output_file = Path(output_file)
    json_files = sorted(by_letter_dir.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(f"No .json files found in {by_letter_dir}")

    for json_file in json_files:
        letter = json_file.stem.lower()
        if len(letter) != 1 or not (letter.isalnum() or letter == "_"):
            continue
        print(f"Processing {letter}.json...", end=" ")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Expected top-level JSON object to be a dictionary in {json_file.name}")

        entries = data.get("dictionary_entries", [])
        if not isinstance(entries, list):
            raise ValueError(f"Expected 'dictionary_entries' to be a list in {json_file.name}")
        keyword_count = 0

        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"Expected entry to be a dict in {json_file.name}")
            gloss_en = entry.get("gloss_en")
            if not isinstance(gloss_en, str):
                continue
            gloss_en = gloss_en.strip()
            if not gloss_en:
                continue

            keywords = tokenize_gloss(gloss_en)
            for kw in keywords:
                index[kw].add(letter)
                keyword_count += 1

        print(f"{len(entries)} entries, {keyword_count} keywords indexed")

    print(f"\nTotal unique keywords: {len(index)}")

    output_dict = {kw: sorted(letters) for kw, letters in sorted(index.items())}

    tmp = output_file.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, output_file)

    print(f"Wrote {output_file}")

if __name__ == "__main__":
    by_letter_dir = Path(__file__).parent.parent / "extracted" / "dictionary" / "by-letter"
    output_file = Path(__file__).parent.parent / "extracted" / "dictionary" / "gloss_index.json"

    if not by_letter_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {by_letter_dir}")

    build_gloss_index(by_letter_dir, output_file)
