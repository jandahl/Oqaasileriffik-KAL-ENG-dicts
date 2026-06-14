## Conversion Pipeline

This directory contains the ODS → JSON conversion pipeline for the Kalaallisut–English dictionary.

See root README.md for full workflow.

### Files

- `convert.py` — Main pipeline script; runs the full build end-to-end
- `build_gloss_index.py` — Inverted EN keyword index builder; called by `convert.py`
- `requirements.txt` — Python dependencies (odfpy, jsonschema)
- `schema.json` — JSON Schema used to validate the full data bundle before writing
- `COLUMN_MAP_NOTES.md` — Column mapping documentation
- `authored_presets.json` — Hand-curated sandhi examples (empty until populated)

Run `python convert/convert.py --inspect "2018 Chicago/A.ods"` to explore columns.
