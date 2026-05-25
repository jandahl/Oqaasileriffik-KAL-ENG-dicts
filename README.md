# Oqaasileriffik KAL–ENG Dicts (fork)

Fork of [Oqaasileriffik/dicts](https://github.com/Oqaasileriffik/dicts), the
Greenlandic Language Secretariat's 2018 Chicago Kalaallisut–English dictionary.

This fork adds a conversion pipeline (`convert/`) that extracts lexical data from
the source ODS files and produces `extracted/presets.json`, consumed at runtime by
[jandahl/KalaalliCut](https://github.com/jandahl/KalaalliCut) to populate its
sandhi demo preset cards with real dictionary entries and word-class colors.

---

## Directory layout

```
2018 Chicago/           # upstream source — never modify
LICENSE.txt             # upstream CC-BY-SA 4.0 — never modify
convert/
  convert.py            # ODS → JSON pipeline script
  requirements.txt      # pinned: odfpy, jsonschema
  authored_presets.json # hand-curated sandhi examples (always come first)
  schema.json           # JSON Schema for extracted/presets.json
  COLUMN_MAP_NOTES.md   # documents what each mapped column contains
extracted/
  presets.json          # generated output — committed after every run
  LICENSE               # CC-BY-SA 4.0 derived-work notice
```

---

## Pipeline workflow

### 1. Set up the environment

Always use a virtual environment — never install into the system Python.

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r convert/requirements.txt
```

### 2. (Optional) Inspect column layout after upstream changes

```bash
python convert/convert.py --inspect "2018 Chicago/A.ods"
```

Prints every column header for every sheet and exits. Compare with
`convert/COLUMN_MAP_NOTES.md` to verify the mapping is still valid.

### 3. Run the conversion

```bash
python convert/convert.py
```

Processes every `*.ods` file in `2018 Chicago/`, validates the output against
`convert/schema.json`, and writes `extracted/presets.json` atomically.
Non-zero exit on any error.

### 4. Commit script and output together

```bash
git add convert/ extracted/presets.json
git commit -m "feat(convert): ..."
git push
```

`convert/` changes and `extracted/presets.json` must always be in the same commit.

---

## Output schema

`extracted/presets.json` is a single JSON object:

```json
{
  "meta": {
    "schema_version": "1.0",
    "generated_at": "<ISO-8601-UTC>",
    "license": "CC-BY-SA 4.0",
    "attribution": "Oqaasileriffik (Greenlandic Language Secretariat), ..."
  },
  "sandhi_presets": [ ... ],   // hand-authored examples first, then any generated
  "dictionary_entries": [ ... ]
}
```

Each `dictionary_entries` item has at minimum:
`id`, `lexeme`, `word_class`, `class_path`, `source_file`, `source_row`.

Full schema in `convert/schema.json`.

---

## How KalaalliCut consumes this file

KalaalliCut fetches the file directly from:

```
https://raw.githubusercontent.com/jandahl/Oqaasileriffik-KAL-ENG-dicts/main/extracted/presets.json
```

**Do not split `extracted/presets.json` into multiple files** — KalaalliCut
expects a single monolithic JSON document.

---

## License obligations

The source dictionary is released under
**CC-BY-SA 4.0** by Oqaasileriffik (Greenlandic Language Secretariat).

Required attribution text (must appear in any derivative work):

> Oqaasileriffik (Greenlandic Language Secretariat), 2018 Chicago
> Kalaallisut–English Dictionary, CC-BY-SA 4.0

**ShareAlike** means any derivative work — including `extracted/presets.json` and
any downstream product that incorporates it (such as KalaalliCut) — must be
released under CC-BY-SA 4.0 or a compatible license.

---

## Syncing upstream changes

```bash
git remote add upstream https://github.com/Oqaasileriffik/dicts
git fetch upstream
git merge upstream/main
```

After merging, re-run `--inspect` to confirm column layout is unchanged, then
rerun the conversion and commit the updated output.
