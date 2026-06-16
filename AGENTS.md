# AGENTS.md - Instructions for AI Agents / Collaborators

## Purpose
This repo maintains the conversion pipeline from Oqaasileriffik ODS dictionary files to `extracted/presets.json` used by KalaalliCut.

## Rules for Agents
- NEVER modify files in `2018 Chicago/` or `LICENSE.txt`
- Always run full conversion + validation before committing `extracted/presets.json`
- Commit `kal_eng_dicts/` changes and `extracted/presets.json` in SAME commit
- Use atomic writes and schema validation via the `oqaasileriffik-pipeline` in `kal_eng_dicts/ODS_lexeme_extractor.py`
- Update `COLUMN_MAP_NOTES.md` whenever COLUMN_MAP changes
- Follow commit discipline and logging rules from handover
- For changes: inspect columns first if upstream updated

## Architecture and Python Packaging Lessons
- **Hyphens in Module Names:** When creating `console_scripts` entry points in `pyproject.toml`, the module path must be a valid Python import path. Do not use hyphens in filenames or directory names (e.g., use `kal_eng_dicts/ODS_lexeme_extractor.py`, not `ODS-lexeme-extractor`).
- **`__init__.py` Required:** Any directory listed in `tool.setuptools.packages` must contain an `__init__.py` file to ensure `setuptools` packages it properly.
- **Pre-flight Checks:** Validate the existence of `schema.json` using `path.is_file()` *before* invoking `Pipeline(...)`. This prevents the pipeline from raising generic `ValueError`s during initialization and allows for clean `FileNotFoundError`s.
- **Exception Logging:** When adding fallback `except Exception` blocks, always use `log.exception(...)` instead of `log.error(...)` to preserve the stack trace. However, you should also specifically catch `jsonschema.ValidationError` to suppress redundant tracebacks since `Pipeline.run()` logs schema violations gracefully.
- **CLI Testability:** Construct `main()` and underlying implementation functions to accept an optional `argv: list[str] | None = None` argument so they can be unit-tested without mocking `sys.argv`. Have `main()` return an integer exit code rather than calling `sys.exit()` directly, reserving the `sys.exit()` call exclusively for the `if __name__ == "__main__":` execution block.

Refer to the detailed handover document in the initial issue/PR or commit history for full spec.
