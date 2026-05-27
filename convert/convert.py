import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import argparse

from build_gloss_index import build_gloss_index

from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P

import jsonschema

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s %(message)s',
)
log = logging.getLogger(__name__)

# Inspected against 2018 Chicago/A.ods — col 2 header "Tuluttuua" is used to
# identify the main gloss sheet across all ODS files (see COLUMN_MAP_NOTES.md).
COLUMN_MAP: dict[str, int] = {
    "lexeme":      0,   # "Ujartugassaq" / "Kalaallisut"
    "word_class":  1,   # "Suussusaa" / "Suussusia"
    "stem":        -1,  # no stem column in these files
    "valence":     -1,
    "sandhi_type": -1,
    "gloss_en":    2,   # "Tuluttuua"
}

# Word-class header found in col 2 of the main gloss sheet; other values
# indicate a non-gloss sheet that should be skipped.
GLOSS_SHEET_MARKER = "Tuluttuua"

# Kalaallisut word-class terms as they appear in col 1 of the main gloss sheet.
WORD_CLASS_TO_PATH: dict[str, list[str]] = {
    # English abbreviations (may appear in minor sheets; lowercased for lookup)
    "n":                              ["nominal_root", "common_noun"],
    "prop":                           ["nominal_root", "proper_noun"],
    "pron":                           ["nominal_root", "pronoun"],
    "v":                              ["verbal_root"],
    "v_h":                            ["verbal_root", "intransitive"],
    "v_t":                            ["verbal_root", "transitive"],
    "v_i":                            ["verbal_root", "intransitive"],
    "pali":                           ["enclitic"],
    "conj":                           ["enclitic"],
    "adv":                            ["enclitic"],
    "interj":                         ["enclitic"],
    "num":                            ["nominal_root", "common_noun"],
    "symbol":                         ["nominal_root"],
    # Kalaallisut terms from actual ODS files (all keys are lowercase;
    # lookup is case-insensitive — see parse_ods_file)
    "taggit":                                ["nominal_root", "common_noun"],
    "taggit qasseersiut":                    ["nominal_root", "common_noun"],
    "taggit qasseersiut (ataas inuak)":      ["nominal_root", "common_noun"],
    "taggit qasseersiut (ataas qajaq)":      ["nominal_root", "common_noun"],
    "taggit qasseersiut (ataas saaneq)":     ["nominal_root", "common_noun"],
    "taggit qasseersiut (ataas sanik)":      ["nominal_root", "common_noun"],
    "taggit (naal qupp.)":                   ["nominal_root", "common_noun"],
    "taggit ataasersiut":                    ["nominal_root", "common_noun"],
    "taggit atiusoq":                        ["nominal_root", "proper_noun"],
    "t qass":                                ["nominal_root", "common_noun"],   # truncated
    "proprium/egennavn":                     ["nominal_root", "proper_noun"],
    "stednavn":                              ["nominal_root", "proper_noun"],   # Danish: place name
    "oqaluut":                               ["verbal_root"],
    "oqaluut susaatsoq":                     ["verbal_root", "transitive"],
    "oqaluut susaatsoq qasseersiut":         ["verbal_root", "transitive"],
    "oqaluut susaatsq":                      ["verbal_root", "transitive"],   # typo
    "oqaluut susaatsot":                     ["verbal_root", "transitive"],   # typo
    "oqaluut susaatoq":                      ["verbal_root", "transitive"],   # typo
    "oqaluut suaatsoq":                      ["verbal_root", "transitive"],   # typo
    "oqaluut susaaatsoq":                    ["verbal_root", "transitive"],   # typo
    "oqaluut susaatsoq (taggit)":            ["verbal_root", "transitive"],
    "oqaluut susaatsoq plus htr??":          ["verbal_root", "transitive"],
    "oqaluut susalik":                       ["verbal_root", "intransitive"],
    "oqlauut susalik":                       ["verbal_root", "intransitive"],  # typo
    "oqaluut susasalik":                     ["verbal_root", "intransitive"],  # typo
    "oqaluut sasalik":                       ["verbal_root", "intransitive"],  # typo
    "oqaluut susalik (oqaluut susaasalik)":  ["verbal_root", "intransitive"],
    "oqaluut susaasalik":                    ["verbal_root", "intransitive"],
    "oqaluut aappiuttartoq":                 ["verbal_root"],
    "oqaluut pisimasorsiut":                 ["verbal_root"],
    "oqaluut taggisaasaq":                   ["verbal_root"],
    "oqaluut inatsiniut":                    ["verbal_root"],
    "o/i":                                   ["verbal_root", "intransitive"],
    "oqaaseeraq":                            ["enclitic"],
    "oqaaseeraq kattut":                     ["enclitic"],
    "oqaaseeraq oqaqqarniut":                ["enclitic"],
}


def get_cell_text(cell) -> str:
    """Extract text content from an ODF TableCell."""
    parts = []
    for p in cell.getElementsByType(P):
        for child in p.childNodes:
            if hasattr(child, 'data'):
                parts.append(child.data)
    return ''.join(parts).strip()


def is_gloss_sheet(sheet) -> bool:
    """Return True only for sheets whose header row has GLOSS_SHEET_MARKER in col 2."""
    rows = sheet.getElementsByType(TableRow)
    if not rows:
        return False
    header_cells = rows[0].getElementsByType(TableCell)
    if len(header_cells) < 3:
        return False
    return get_cell_text(header_cells[2]) == GLOSS_SHEET_MARKER


def parse_ods_file(filepath: Path, column_map: dict) -> list[dict]:
    """Parse one .ods file — only processes sheets identified as gloss sheets."""
    doc = load(str(filepath))
    entries = []

    for sheet in doc.getElementsByType(Table):
        sheet_name = sheet.getAttribute('name') or 'unknown'
        if not is_gloss_sheet(sheet):
            log.debug("Skipping sheet %r in %s (not a gloss sheet)", sheet_name, filepath.name)
            continue

        rows = sheet.getElementsByType(TableRow)
        for row_idx, row in enumerate(rows[1:], start=1):  # row 0 is header
            cells = row.getElementsByType(TableCell)
            if not cells:
                continue

            entry: dict = {
                "id": f"{filepath.stem}_{sheet_name}_{row_idx + 1}",
                "lexeme": "",
                "word_class": "",
                "class_path": [],
                "stem": "",
                "gloss_en": "",
                "source_file": filepath.name,
                "source_row": row_idx + 1,
            }

            for key, col_idx in column_map.items():
                if col_idx < 0 or col_idx >= len(cells):
                    continue
                text = get_cell_text(cells[col_idx])
                if key in entry:
                    entry[key] = text

            wc = entry["word_class"].strip()
            wc_key = wc.lower()
            if wc_key in WORD_CLASS_TO_PATH:
                entry["class_path"] = WORD_CLASS_TO_PATH[wc_key]
            elif wc:
                log.warning(
                    "Unknown word_class %r in %s sheet %r row %d",
                    wc, filepath.name, sheet_name, row_idx + 1,
                )

            if not entry["stem"]:
                entry["stem"] = entry["lexeme"]

            if entry["lexeme"]:
                entries.append(entry)

    return entries


def load_authored_presets(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        log.warning("Failed to load authored_presets: %s", e)
        return []


def validate_output(data: dict, schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    jsonschema.validate(instance=data, schema=schema)
    log.info("Schema validation passed")


def write_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="ODS -> KalaalliCut presets.json converter")
    parser.add_argument('--inspect', metavar='ODS_FILE',
                        help='Print column headers for every sheet in ODS_FILE and exit')
    parser.add_argument('--generate-stubs', action='store_true',
                        help='Generate root stubs from dictionary entries (placeholder)')
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.resolve()
    convert_dir = repo_root / "convert"
    ods_dir = repo_root / "2018 Chicago"
    extracted_dir = repo_root / "extracted" / "dictionary"
    schema_path = convert_dir / "schema.json"
    authored_path = convert_dir / "authored_presets.json"

    if args.inspect:
        filepath = Path(args.inspect)
        if not filepath.exists():
            log.error("File not found: %s", filepath)
            sys.exit(1)
        print(f"\n=== Inspecting columns in {filepath} ===")
        doc = load(str(filepath))
        for sheet in doc.getElementsByType(Table):
            name = sheet.getAttribute('name') or 'Unnamed'
            print(f"\nSheet: {name}")
            rows = sheet.getElementsByType(TableRow)
            if rows:
                for i, cell in enumerate(rows[0].getElementsByType(TableCell)):
                    print(f"  {i:2d}: {get_cell_text(cell)}")
        return

    log.info("Starting ODS conversion pipeline")

    extracted_dir.mkdir(exist_ok=True)
    by_letter_dir = extracted_dir / "by-letter"
    by_letter_dir.mkdir(exist_ok=True)

    # Per-ODS parse cache (gitignored). Each file stores the raw entries list
    # for one ODS file; avoids re-parsing unchanged sources.
    cache_dir = extracted_dir / ".cache"
    cache_dir.mkdir(exist_ok=True)

    ods_paths = sorted(ods_dir.glob("*.ods"))
    if not ods_paths:
        raise FileNotFoundError(f"No ODS files found in {ods_dir}")
    max_ods_mtime = max(p.stat().st_mtime for p in ods_paths)

    # generated_at is derived from source mtimes so re-running on unchanged
    # files produces byte-identical JSON and a clean git diff.
    meta = {
        "schema_version": "1.0",
        "generated_at": datetime.fromtimestamp(max_ods_mtime, tz=timezone.utc).isoformat(),
        "license": "CC-BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "source_repo": "https://github.com/Oqaasileriffik/dicts",
        "fork_repo": "https://github.com/jandahl/Oqaasileriffik-KAL-ENG-dicts",
        "attribution": "Oqaasileriffik (Greenlandic Language Secretariat), 2018 Chicago Kalaallisut–English Dictionary, CC-BY-SA 4.0",
        "changes": "Subset of entries extracted and reformatted; class_path fields added for KalaalliCut color mapping.",
    }

    all_entries: list[dict] = []
    script_mtime = Path(__file__).stat().st_mtime

    for ods_path in ods_paths:
        cache_path = cache_dir / f"{ods_path.stem}.json"
        ods_mtime = ods_path.stat().st_mtime

        if cache_path.exists() and cache_path.stat().st_mtime >= max(ods_mtime, script_mtime):
            try:
                log.info("Skipping %s (cache up to date)", ods_path.name)
                all_entries.extend(json.loads(cache_path.read_text(encoding='utf-8')))
                continue
            except (json.JSONDecodeError, OSError) as e:
                log.warning("Cache read failed for %s (%s), re-parsing", ods_path.name, e)

        log.info("Parsing %s ...", ods_path.name)
        entries = parse_ods_file(ods_path, COLUMN_MAP)
        log.info("  -> %d entries", len(entries))
        all_entries.extend(entries)

        tmp = cache_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(entries, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, cache_path)
        any_parsed = True

    log.info("Total dictionary_entries: %d", len(all_entries))

    sandhi_presets = load_authored_presets(authored_path)
    log.info("Loaded %d hand-authored sandhi presets", len(sandhi_presets))

    validate_output(
        {"meta": meta, "sandhi_presets": sandhi_presets, "dictionary_entries": all_entries},
        schema_path,
    )

    presets_path = extracted_dir / "presets.json"
    write_atomic(presets_path, {"meta": meta, "sandhi_presets": sandhi_presets})
    log.info("Wrote %s (%d sandhi presets)", presets_path, len(sandhi_presets))

    all_entries_path = extracted_dir / "all_entries.json"
    gloss_index_path = extracted_dir / "gloss_index.json"

    grouped: dict[str, list] = {}
    for entry in all_entries:
        lexeme = entry.get("lexeme", "")
        letter = lexeme[0].lower() if lexeme else "_"
        grouped.setdefault(letter, []).append(entry)

    # Always write outputs — code changes to convert.py or build_gloss_index.py
    # must be reflected even when ODS files are unchanged. Deterministic
    # generated_at means unchanged sources produce identical JSON (clean git diff).
    for letter, entries in sorted(grouped.items()):
        letter_path = by_letter_dir / f"{letter}.json"
        write_atomic(letter_path, {"meta": meta, "dictionary_entries": entries})
        log.info("Wrote %s (%d entries)", letter_path, len(entries))

    log.info("Wrote %d by-letter files", len(grouped))

    write_atomic(all_entries_path, {"meta": meta, "dictionary_entries": all_entries})
    log.info("Wrote %s (%d total entries)", all_entries_path, len(all_entries))

    build_gloss_index(by_letter_dir, gloss_index_path)
    log.info("Wrote %s", gloss_index_path)

    if args.generate_stubs:
        log.info("--generate-stubs requested (not yet implemented)")


if __name__ == "__main__":
    main()
