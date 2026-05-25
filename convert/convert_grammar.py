import os
import sys
import copy
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import argparse

import yaml
import jsonschema

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s %(message)s',
)
log = logging.getLogger(__name__)


def deep_merge(base: dict, override: dict) -> dict:
    """Return a new dict: override merged into a deep copy of base."""
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def load_templates(path: Path) -> dict:
    if not path.exists():
        log.warning("No templates.yaml found at %s", path)
        return {}
    raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    return raw if isinstance(raw, dict) else {}


def resolve_entry(entry: dict, templates: dict) -> dict:
    entry = copy.deepcopy(entry)
    template_name = entry.pop('_template', None)
    if template_name is None:
        return entry
    if template_name not in templates:
        log.warning("Unknown template %r", template_name)
        return entry
    return deep_merge(templates[template_name], entry)


def load_data_dir(data_dir: Path, templates: dict) -> tuple[dict, list]:
    by_category: dict = {}
    flat: list = []

    for yaml_path in sorted(data_dir.rglob('*.yaml')):
        if yaml_path.name == 'templates.yaml':
            continue

        category = yaml_path.stem
        raw = yaml.safe_load(yaml_path.read_text(encoding='utf-8')) or {}
        morphemes = raw.get('morphemes')
        if not morphemes:
            log.warning("No 'morphemes' key in %s — skipping", yaml_path.name)
            continue

        resolved: dict = {}
        for morpheme_id, entry in morphemes.items():
            if not isinstance(entry, dict):
                log.warning("Skipping non-dict entry %r in %s", morpheme_id, yaml_path.name)
                continue
            entry = resolve_entry(entry, templates)
            entry['id'] = morpheme_id
            entry['category'] = category
            resolved[morpheme_id] = entry
            flat.append(entry)

        by_category[category] = resolved
        log.info("Loaded %d morphemes from %s", len(resolved), yaml_path.name)

    return by_category, flat


def validate_output(data: dict, schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    jsonschema.validate(instance=data, schema=schema)
    log.info("Schema validation passed")


def write_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="YAML grammar data -> morphemes.json converter")
    parser.add_argument('--list-templates', action='store_true',
                        help='Print available template names and exit')
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.resolve()
    convert_dir = repo_root / 'convert'
    data_dir = repo_root / 'kalaallisut_data'
    schema_path = convert_dir / 'grammar_schema.json'
    out_dir = repo_root / 'extracted' / 'grammar'
    out_path = out_dir / 'morphemes.json'

    templates = load_templates(data_dir / 'templates.yaml')

    if args.list_templates:
        for name in sorted(templates):
            print(name)
        return

    if not data_dir.exists():
        log.error("Data directory not found: %s", data_dir)
        sys.exit(1)

    log.info("Starting grammar conversion pipeline")

    by_category, flat = load_data_dir(data_dir, templates)

    total = len(flat)
    log.info("Total morphemes: %d across %d categories", total, len(by_category))

    data = {
        'meta': {
            'schema_version': '1.0',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'license': 'CC-BY-SA 4.0',
            'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'fork_repo': 'https://github.com/jandahl/Oqaasileriffik-KAL-ENG-dicts',
            'attribution': 'Hand-authored grammar data for KalaalliCut, CC-BY-SA 4.0',
            'note': 'by_category and flat contain the same morphemes in different shapes.',
        },
        'by_category': by_category,
        'flat': flat,
    }

    validate_output(data, schema_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_atomic(out_path, data)
    log.info("Wrote %s (%d morphemes)", out_path, total)


if __name__ == '__main__':
    main()
