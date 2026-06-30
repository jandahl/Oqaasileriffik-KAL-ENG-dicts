# Oqaasileriffik KAL–ENG Dicts (fork)

Fork of [Oqaasileriffik/dicts](https://github.com/Oqaasileriffik/dicts), the
Greenlandic Language Secretariat's 2018 Chicago Kalaallisut–English dictionary.

This fork adds a conversion pipeline (`convert/`) that extracts lexical data from
the source ODS files and produces structured JSON consumed by
[jandahl/KalaalliCut](https://github.com/jandahl/KalaalliCut).

---

## Directory layout

```
2018 Chicago/               # upstream source — never modify
LICENSE.txt                 # upstream CC-BY-SA 4.0 — never modify
convert/
  convert.py                # ODS → JSON pipeline (runs the full pipeline)
  build_gloss_index.py      # inverted EN keyword index (called by convert.py)
  requirements.txt          # pinned: odfpy, jsonschema
  authored_presets.json     # hand-curated sandhi examples
  schema.json               # JSON Schema for full data bundle validation
  COLUMN_MAP_NOTES.md       # documents what each mapped column contains
extracted/
  dictionary/
    presets.json            # {meta, sandhi_presets} — committed after every run
    all_entries.json        # {meta, dictionary_entries} — all entries in one file
    gloss_index.json        # inverted EN keyword → [starting letters] index
    by-letter/
      a.json … z.json       # {meta, dictionary_entries} split by first letter
    LICENSE                 # CC-BY-SA 4.0 derived-work notice
```

---

## Pipeline workflow

### 1. Set up the environment

Always use a virtual environment — never install into the system Python.

> [!WARNING]
> **Windows environments (including MSYS2, Cygwin, and MinGW) are explicitly NOT supported.**
> Do not attempt to run this pipeline or install dependencies on a Windows machine.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r convert/requirements.txt
```

### 2. (Optional) Inspect column layout after upstream changes

```bash
python convert/convert.py --inspect "2018 Chicago/A.ods"
```

Prints every column header for every sheet and exits. Compare with
`convert/COLUMN_MAP_NOTES.md` to verify the mapping is still valid.

### 3. Run the full pipeline

```bash
python convert/convert.py
```

This single command:

1. Parses every `*.ods` file in `2018 Chicago/`
2. Validates the full data bundle against `convert/schema.json`
3. Writes `extracted/dictionary/presets.json` — `{meta, sandhi_presets}`
4. Writes `extracted/dictionary/all_entries.json` — `{meta, dictionary_entries}` (all entries)
5. Writes `extracted/dictionary/by-letter/*.json` — entries split by first letter of lexeme
6. Builds `extracted/dictionary/gloss_index.json` — inverted EN keyword → starting-letter index

Non-zero exit on any error.

### 4. Commit scripts and output together

```bash
git add convert/ extracted/dictionary/
git commit -m "feat(convert): ..."
git push
```

All `convert/` changes and generated output files must always be in the same commit.

---

## Output files

### `presets.json`

Sandhi presets only — small file loaded on every KalaalliCut page load.

```json
{
  "meta": { "schema_version": "1.0", "generated_at": "<ISO-8601-UTC>", ... },
  "sandhi_presets": [ ... ]
}
```

### `all_entries.json`

Full dictionary — use when you need all entries without issuing per-letter requests.

```json
{
  "meta": { ... },
  "dictionary_entries": [ ... ]
}
```

### `by-letter/{letter}.json`

One file per starting letter of lexeme. Same `{meta, dictionary_entries}` shape as
`all_entries.json`. Use for lazy/partial loading.

### `gloss_index.json`

Inverted index of English keywords → sorted list of Kalaallisut starting letters.
Compact minified JSON (~291 KB uncompressed).

The root is a one-level `{meta, index}` wrapper so license/version metadata can be
carried inline without colliding with keyword keys (the keyword map lives under
`index`):

```json
{
  "meta": { "version": "1.0", "license": "CC-BY-SA-4.0", "generated_at": "…" },
  "index": { "dream": ["s"], "sleep": ["a", "i", "s", "t", "u"], ... }
}
```

Each `dictionary_entries` item has at minimum:
`id`, `lexeme`, `word_class`, `class_path`, `source_file`, `source_row`.

Full schema in `convert/schema.json`.

---

## GH Pages URLs

All output files are published on every push to `main` that changes anything under
`extracted/dictionary/`:

```
https://jandahl.github.io/Oqaasileriffik-KAL-ENG-dicts/presets.json
https://jandahl.github.io/Oqaasileriffik-KAL-ENG-dicts/all_entries.json
https://jandahl.github.io/Oqaasileriffik-KAL-ENG-dicts/gloss_index.json
https://jandahl.github.io/Oqaasileriffik-KAL-ENG-dicts/by-letter/a.json
```

---

## License obligations

The source dictionary is released under
**CC-BY-SA 4.0** by Oqaasileriffik (Greenlandic Language Secretariat).

Required attribution text (must appear in any derivative work):

> Oqaasileriffik (Greenlandic Language Secretariat), 2018 Chicago
> Kalaallisut–English Dictionary, CC-BY-SA 4.0

**ShareAlike** means any derivative work — including the generated JSON files and
any downstream product that incorporates them (such as KalaalliCut) — must be
released under CC-BY-SA 4.0 or a compatible license.

---

## Syncing upstream changes

```bash
git remote add upstream https://github.com/Oqaasileriffik/dicts
git fetch upstream
git merge upstream/main
```

After merging, re-run `--inspect` to confirm column layout is unchanged, then
rerun the pipeline and commit the updated output.
