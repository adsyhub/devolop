"""Validate and synchronize canonical offline schema resources."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    canonical = {p.name: p for p in (root / 'schemas').glob('*.json')}
    target = root / 'eju_bank/schemas'
    ids = set()
    for name, path in canonical.items():
        schema = json.loads(path.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        if not schema.get('$id') or schema['$id'] in ids:
            raise SystemExit(f'Missing/duplicate schema ID: {name}')
        ids.add(schema['$id'])
    if args.check:
        if {p.name for p in target.glob('*.json')} != set(canonical):
            raise SystemExit('Schema resource file list differs')
        for name, path in canonical.items():
            if (target / name).read_bytes() != path.read_bytes():
                raise SystemExit(f'Schema resource is stale: {name}')
    else:
        target.mkdir(exist_ok=True)
        for name, path in canonical.items():
            (target / name).write_bytes(path.read_bytes())
        for path in target.glob('*.json'):
            if path.name not in canonical:
                path.unlink()


if __name__ == '__main__':
    main()
