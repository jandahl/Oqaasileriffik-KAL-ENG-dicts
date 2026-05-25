# Full implementation of the ODS → JSON conversion pipeline for KalaalliCut

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
try:
    from odf.opendocument import load
    from odf.table import TableRow, TableCell
except ImportError:
    print("Error: odfpy is required. Install with: pip install -r convert/requirements.txt")
    sys.exit(1)

# Configure logging to stdout only
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s %(message)s',
)
log = logging.getLogger(__name__)

# Column mapping - updated from inspection of 2018 Chicago/*.ods files
# Danish headers observed:
# 0: Kalaallisut (lexeme)
# 1: Ordklasse (word_class)
# 2: Stamme (stem)
# 3: Engelsk (gloss_en)
COLUMN_MAP: Dict[str, int] = {
    "lexeme": 0,
    "word_class": 1,
    "stem": 2,
    "valence": -1,      # not present
    "sandhi_type": -1,  # not present
    "gloss_en": 3,
}

WORD_CLASS_TO_PATH: Dict[str, List[str]] = {
    "N": ["nominal_root", "common_noun"],
    "Prop": ["nominal_root", "proper_noun"],
    "Pron": ["nominal_root", "pronoun"],
    "V": ["verbal_root"],
    "V_H": ["verbal_root", "intransitive"],
    "V_T": ["verbal_root", "transitive"],
    "V_I": ["verbal_root", "intransitive"],
    "Pali": ["enclitic"],
    "Conj": ["enclitic"],
    "Adv": ["enclitic"],
    "Interj": ["enclitic"],
    "Num": ["nominal_root", "common_noun"],
    "Symbol": ["nominal_root"],
}


def get_cell_text(cell: Optional[TableCell]) -> str:
    """Extract text from an ODF table cell."""
    if cell is None:
        return ""
    text = ""
    for child in cell.childNodes:
        if hasattr(child, 'data'):
            text += child.data
        elif hasattr(child, 'text'):
            text += child.text or ""
    return text.strip()


def load_ods_file(filepath: Path) -> List[List[str]]:
    """Load all rows from all sheets in an ODS file."""
    doc = load(str(filepath))
    all_rows = []
    for sheet in doc.getElementsByType(Table):
        for row in sheet.getElementsByType(TableRow):
            row_data = []
            cells = row.getElementsByType(TableCell)
            for cell in cells:
                text = get_cell_text(cell)
                row_data.append(text)
            if row_data:  # skip empty rows
                all_rows.append(row_data)
    return all_rows


def inspect_ods(filepath: str) -> None:
    """Inspect column headers and sample data."""
    path = Path(filepath)
    if not path.exists():
        log.error("File not found: %s", filepath)
        sys.exit(1)

    print(f"\n=== INSPECTING {path.name} ===")
    rows = load_ods_file(path)
    if not rows:
        print("No data found.")
        return

    headers = rows[0]
    print("\nColumn headers (index: header):")
    for i, h in enumerate(headers):
        print(f"  {i:2d}: {h}")

    print("\nFirst 5 data rows (first 8 columns):")
    for i in range(1, min(6, len(rows))):
        row = rows[i][:8]
        print(f"  {i:2d}: {row}")


def get_class_path(word_class: str) -> List[str]:
    """Map word_class code to class_path list."""
    if not word_class:
        return []
    wc = word_class.strip()
    if wc in WORD_CLASS_TO_PATH:
        return WORD_CLASS_TO_PATH[wc]
    log.warning("Unknown word_class %r → class_path: []", wc)
    return []


def write_atomic(path: Path, data: Dict) -> None:
    """Write JSON atomically to prevent partial/corrupt files."""
    tmp = path.with_suffix('.tmp')
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    os.replace(tmp, path)


def validate_output(data: Dict, schema_path: Path) -> None:
    """Validate generated JSON against schema."""
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    jsonschema.validate(instance=data, schema=schema)
    log.info("Schema validation passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="ODS → presets.json converter for KalaalliCut")
    parser.add_argument('--inspect', help='Inspect ODS file columns and exit')
    parser.add_argument('--generate-stubs', action='store_true', help='Generate root stubs')
    args = parser.parse_args()

    if args.inspect:
        inspect_ods(args.inspect)
        return

    # Defensive check: refuse to modify upstream
    upstream_dir = Path("2018 Chicago")
    if upstream_dir.exists() and any(p.is_file() for p in upstream_dir.rglob("*")):
        for f in upstream_dir.rglob("*"):
            if "convert" in str(f).lower() or "extracted" in str(f).lower():
                continue
            log.error("Refusing to run: upstream source files in '2018 Chicago/' must NEVER be modified")
            sys.exit(1)

    log.info("Starting ODS → JSON conversion pipeline...")

    # Find all ODS files
    ods_dir = Path("2018 Chicago")
    ods_files = list(ods_dir.glob("*.ods"))
    if not ods_files:
        log.error("No .ods files found in '2018 Chicago/' directory")
        sys.exit(1)

    dictionary_entries: List[Dict] = []
    entry_id = 0

    for ods_file in sorted(ods_files):
        log.info("Processing %s", ods_file.name)
        rows = load_ods_file(ods_file)
        if not rows or len(rows) < 2:
            log.warning("No data in %s", ods_file.name)
            continue

        headers = rows[0]
        data_rows = rows[1:]

        for row_idx, row in enumerate(data_rows, start=2):  # 1-based row in ODS
            if len(row) <= max(COLUMN_MAP.values()):
                continue  # too short

            lexeme = row[COLUMN_MAP["lexeme"]].strip() if COLUMN_MAP["lexeme"] >= 0 else ""
            if not lexeme:
                continue  # skip empty lexemes

            word_class = row[COLUMN_MAP["word_class"]].strip() if COLUMN_MAP["word_class"] >= 0 else ""
            stem = row[COLUMN_MAP["stem"]].strip() if COLUMN_MAP["stem"] >= 0 else ""
            if not stem:
                stem = lexeme

            class_path = get_class_path(word_class)

            dictionary_entries.append({
                "id": entry_id,
                "lexeme": lexeme,
                "word_class": word_class,
                "class_path": class_path,
                "source_file": ods_file.name,
                "source_row": row_idx,
            })
            entry_id += 1

    log.info("Extracted %d dictionary entries", len(dictionary_entries))

    # Load authored presets
    authored_path = Path("convert/authored_presets.json")
    if authored_path.exists():
        sandhi_presets = json.loads(authored_path.read_text(encoding='utf-8'))
        log.info("Loaded %d authored sandhi presets", len(sandhi_presets))
    else:
        sandhi_presets = []
        log.warning("authored_presets.json not found")

    # Build final output
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "meta": {
            "schema_version": "1.0",
            "generated_at": now,
            "license": "CC-BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source_repo": "https://github.com/Oqaasileriffik/dicts",
            "fork_repo": "https://github.com/jandahl/Oqaasileriffik-KAL-ENG-dicts",
            "attribution": "Oqaasileriffik (Greenlandic Language Secretariat), 2018 Chicago Kalaallisut–English Dictionary, CC-BY-SA 4.0",
            "changes": "Subset of entries extracted and reformatted; class_path fields added for KalaalliCut color mapping."
        },
        "sandhi_presets": sandhi_presets,
        "dictionary_entries": dictionary_entries
    }

    # Validate
    schema_path = Path("convert/schema.json")
    validate_output(data, schema_path)

    # Atomic write
    output_path = Path("extracted/presets.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(output_path, data)

    log.info("Successfully wrote %s (%d dictionary entries)", output_path, len(dictionary_entries))


if __name__ == "__main__":
    main()
