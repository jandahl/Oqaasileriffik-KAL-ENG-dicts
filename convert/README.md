## Conversion Pipeline

This directory contains the ODS → JSON conversion pipeline for the Kalaallisut–English dictionary.

See root README.md for full workflow.

### Files
- `convert.py` - Main conversion script
- `requirements.txt` - Python dependencies
- `schema.json` - JSON Schema for output
- `COLUMN_MAP_NOTES.md` - Column mapping documentation
- `authored_presets.json` - Curated sandhi examples

Run `python convert/convert.py --inspect "2018 Chicago/A.ods"` to explore columns.