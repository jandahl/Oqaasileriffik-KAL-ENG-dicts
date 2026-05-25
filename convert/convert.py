import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import argparse

from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P

import jsonschema

# Setup logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s %(message)s',
)
log = logging.getLogger(__name__)

# COLUMN_MAP - pre-filled from COLUMN_MAP_NOTES.md inspection of Danish headers
COLUMN_MAP: dict[str, int | None] = {
    "lexeme":      0,   # Kalaallisut
    "word_class":  1,   # Ordklasse
    "stem":        2,   # Stamme
    "valence":     -1,
    "sandhi_type": -1,
    "gloss_en":    3,   # Engelsk
}

WORD_CLASS_TO_PATH: dict[str, list[str]] = {
    "N":      ["nominal_root", "common_noun"],
    "Prop":   ["nominal_root", "proper_noun"],
    "Pron":   ["nominal_root", "pronoun"],
    "V":      ["verbal_root"],
    "V_H":    ["verbal_root", "intransitive"],
    "V_T":    ["verbal_root", "transitive"],
    "V_I":    ["verbal_root", "intransitive"],
    "Pali":   ["enclitic"],
    "Conj":   ["enclitic"],
    "Adv":    ["enclitic"],
    "Interj": ["enclitic"],
    "Num":    ["nominal_root", "common_noun"],
    "Symbol": ["nominal_root"],
}

def get_cell_text(cell):
    """Extract text from ODF TableCell."""
    if not cell:
        return ""
    text_parts = []
    for p in cell.getElementsByType(P):
        for child in p.childNodes:
            if hasattr(child, 'data'):
                text_parts.append(child.data)
    # Fallback for direct text
    for child in cell.childNodes:
        if hasattr(child, 'data'):
            text_parts.append(child.data)
    return ''.join(text_parts).strip()

def parse_ods_file(filepath: Path, column_map: dict) -> list[dict]:
    """Parse one .ods file into dictionary entries."""
    doc = load(str(filepath))
    entries = []
    
    for sheet in doc.getElementsByType(Table):
        sheet_name = sheet.getAttribute('name') or 'unknown'
        log.debug(f"Processing sheet '{sheet_name}' in {filepath.name}")
        
        rows = sheet.getElementsByType(TableRow)
        if not rows:
            continue
            
        # row 0 is header
        for row_idx, row in enumerate(rows[1:], start=1):
            cells = row.getElementsByType(TableCell)
            if len(cells) == 0:
                continue
                
            entry = {
                "id": f"{filepath.stem}_{sheet_name}_{row_idx+1}",
                "lexeme": "",
                "word_class": "",
                "class_path": [],
                "stem": "",
                "gloss_en": "",
                "source_file": filepath.name,
                "source_row": row_idx + 1,  # 1-based
            }
            
            for key, col_idx in column_map.items():
                if col_idx >= 0 and col_idx < len(cells):
                    text = get_cell_text(cells[col_idx])
                    if key == "lexeme":
                        entry["lexeme"] = text
                    elif key == "word_class":
                        entry["word_class"] = text
                    elif key == "stem":
                        entry["stem"] = text
                    elif key == "gloss_en":
                        entry["gloss_en"] = text
            
            # word class mapping
            wc = entry["word_class"].strip()
            if wc in WORD_CLASS_TO_PATH:
                entry["class_path"] = WORD_CLASS_TO_PATH[wc]
            elif wc:
                log.warning(f"Unknown word_class {wc!r} in {filepath.name} sheet {sheet_name} row {row_idx+1}")
            
            if not entry["stem"]:
                entry["stem"] = entry["lexeme"]
            
            if entry["lexeme"]:
                entries.append(entry)
    
    return entries

def load_authored_presets(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception as e:
            log.warning(f"Failed to load authored_presets: {e}")
    return []

def write_atomic(path: Path, data: dict) -> None:
    """Atomic write using .tmp + os.replace"""
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)

def validate_output(data: dict, schema_path: Path) -> None:
    """Validate against schema.json"""
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    jsonschema.validate(instance=data, schema=schema)
    log.info("✅ JSON schema validation passed")

def main():
    parser = argparse.ArgumentParser(description="ODS → KalaalliCut presets.json converter")
    parser.add_argument('--inspect', metavar='ODS_FILE', help='Inspect column headers of an ODS file and exit')
    parser.add_argument('--generate-stubs', action='store_true', help='Generate additional root stubs (placeholder)')
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.absolute()
    convert_dir = repo_root / "convert"
    ods_dir = repo_root / "2018 Chicago"
    extracted_dir = repo_root / "extracted"
    schema_path = convert_dir / "schema.json"
    authored_path = convert_dir / "authored_presets.json"

    extracted_dir.mkdir(exist_ok=True)

    # Defensive: never touch upstream
    if "2018 Chicago" in str(repo_root) or any(x in sys.argv for x in ["2018 Chicago", "LICENSE.txt"]):
        log.error("🚫 Refusing to modify upstream source files in '2018 Chicago/'")
        sys.exit(1)

    if args.inspect:
        filepath = Path(args.inspect)
        if not filepath.exists():
            log.error(f"File not found: {filepath}")
            sys.exit(1)
        print(f"\n=== Inspecting columns in {filepath} ===")
        doc = load(str(filepath))
        for sheet in doc.getElementsByType(Table):
            name = sheet.getAttribute('name') or 'Unnamed'
            print(f"\nSheet: {name}")
            rows = sheet.getElementsByType(TableRow)
            if rows:
                header = rows[0]
                cells = header.getElementsByType(TableCell)
                for i, cell in enumerate(cells):
                    text = get_cell_text(cell)
                    print(f"  {i:2d}: {text}")
        return

    # Full conversion
    log.info("🚀 Starting ODS conversion pipeline...")

    all_entries: list[dict] = []
    for ods_path in sorted(ods_dir.glob("*.ods")):
        log.info(f"Parsing {ods_path.name}...")
        entries = parse_ods_file(ods_path, COLUMN_MAP)
        all_entries.extend(entries)
        log.info(f"  → extracted {len(entries)} entries")

    log.info(f"Total dictionary_entries: {len(all_entries)}")

    sandhi_presets = load_authored_presets(authored_path)
    log.info(f"Loaded {len(sandhi_presets)} hand-authored sandhi presets")

    data = {
        "meta": {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "license": "CC-BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source_repo": "https://github.com/Oqaasileriffik/dicts",
            "fork_repo": "https://github.com/jandahl/Oqaasileriffik-KAL-ENG-dicts",
            "attribution": "Oqaasileriffik (Greenlandic Language Secretariat), 2018 Chicago Kalaallisut–English Dictionary, CC-BY-SA 4.0",
            "changes": "Subset of entries extracted and reformatted; class_path fields added for KalaalliCut color mapping."
        },
        "sandhi_presets": sandhi_presets,
        "dictionary_entries": all_entries
    }

    validate_output(data, schema_path)

    presets_path = extracted_dir / "presets.json"
    write_atomic(presets_path, data)
    log.info(f"✅ Successfully wrote {presets_path} ({len(all_entries)} dictionary entries)")

    if args.generate_stubs:
        log.info("--generate-stubs requested (placeholder - not yet implemented)")

if __name__ == "__main__":
    main()
