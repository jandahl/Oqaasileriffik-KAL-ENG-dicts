# AGENTS.md - Instructions for AI Agents / Collaborators

## Purpose
This repo maintains the conversion pipeline from Oqaasileriffik ODS dictionary files to `extracted/presets.json` used by KalaalliCut.

## Rules for Agents
- NEVER modify files in `2018 Chicago/` or `LICENSE.txt`
- Always run full conversion + validation before committing `extracted/presets.json`
- Commit `convert/` changes and `extracted/presets.json` in SAME commit
- Use atomic writes and schema validation in `convert.py`
- Update `COLUMN_MAP_NOTES.md` whenever COLUMN_MAP changes
- Follow commit discipline and logging rules from handover
- For changes: inspect columns first if upstream updated

Refer to the detailed handover document in the initial issue/PR or commit history for full spec.
