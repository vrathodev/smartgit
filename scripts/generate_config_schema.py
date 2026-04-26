from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode, JsonSchemaValue

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / 'src'
OUT_DIR = ROOT_DIR / 'docs' / 'generated' / 'schema'

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from smartgit.config import SmartGitConfig


class SmartGitSchemaGenerator(GenerateJsonSchema):
    """Adds a small amount of metadata while preserving source field order."""

    def generate(self, schema: Any, mode: JsonSchemaMode = 'validation') -> JsonSchemaValue:
        json_schema = super().generate(schema, mode=mode)
        json_schema['$schema'] = self.schema_dialect
        json_schema['x-generated-by'] = 'scripts/generate_config_schema.py'
        json_schema['x-schema-mode'] = mode
        return json_schema

    def sort(self, value: JsonSchemaValue, parent_key: str | None = None) -> JsonSchemaValue:
        return value


def _inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Expand local `$ref` nodes and collapse simple nullable `anyOf` forms for readability."""
    definitions = schema.get('$defs', {})

    def resolve(node: Any) -> Any:
        if isinstance(node, list):
            return [resolve(item) for item in node]

        if not isinstance(node, dict):
            return node

        ref = node.get('$ref')
        if isinstance(ref, str) and ref.startswith('#/$defs/'):
            ref_name = ref.rsplit('/', maxsplit=1)[-1]
            resolved = copy.deepcopy(definitions.get(ref_name, {}))
            siblings = {key: value for key, value in node.items() if key != '$ref'}
            if siblings:
                resolved.update({key: resolve(value) for key, value in siblings.items()})
            return resolve(resolved)

        if 'anyOf' in node:
            options = [resolve(item) for item in node['anyOf']]
            non_null_options = [
                item for item in options
                if not (isinstance(item, dict) and item.get('type') == 'null')
            ]
            if len(options) == 2 and len(non_null_options) == 1:
                simplified = copy.deepcopy(non_null_options[0])
                simplified['nullable'] = True
                for key, value in node.items():
                    if key != 'anyOf':
                        simplified[key] = resolve(value)
                return simplified

        return {
            key: resolve(value)
            for key, value in node.items()
            if key != '$defs'
        }

    return resolve(schema)


def _extract_example(schema: dict[str, Any]) -> dict[str, Any]:
    examples = schema.get('examples') or []
    if examples and isinstance(examples[0], dict):
        return examples[0]
    return {}


def _write_json(path: Path, payload: dict[str, Any] | list[Any], indent: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=indent) + '\n', encoding='utf-8')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Generate machine and human-friendly schema artifacts for smartgit.config.json.'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=OUT_DIR / 'smartgit.config.schema.json',
        help='Path for the raw JSON Schema output.',
    )
    parser.add_argument(
        '--expanded-output',
        type=Path,
        default=OUT_DIR / 'smartgit.config.schema.expanded.json',
        help='Path for the human-friendly expanded schema output.',
    )
    parser.add_argument(
        '--example-output',
        type=Path,
        default=OUT_DIR / 'smartgit.config.example.json',
        help='Path for the generated example config output.',
    )
    parser.add_argument(
        '--mode',
        choices=('validation', 'serialization'),
        default='validation',
        help='Pydantic JSON Schema generation mode.',
    )
    parser.add_argument(
        '--indent',
        type=int,
        default=4,
        help='Indentation level used when writing JSON files.',
    )
    parser.add_argument(
        '--skip-expanded',
        action='store_true',
        help='Skip writing the human-friendly expanded schema.',
    )
    parser.add_argument(
        '--skip-example',
        action='store_true',
        help='Skip writing the example config.',
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    raw_schema = SmartGitConfig.model_json_schema(
        mode=args.mode,
        schema_generator=SmartGitSchemaGenerator,
    )
    _write_json(args.output, raw_schema, args.indent)

    if not args.skip_expanded:
        expanded_schema = _inline_refs(raw_schema)
        expanded_schema['x-display-schema'] = True
        expanded_schema['description'] = (
            'Human-friendly view of the SmartGit config schema. '
            'Local $ref values are expanded and simple nullable unions are simplified.'
        )
        _write_json(args.expanded_output, expanded_schema, args.indent)

    if not args.skip_example:
        example_config = _extract_example(raw_schema)
        _write_json(args.example_output, example_config, args.indent)

    print(f'Wrote raw schema to {args.output}')
    if not args.skip_expanded:
        print(f'Wrote expanded schema to {args.expanded_output}')
    if not args.skip_example:
        print(f'Wrote example config to {args.example_output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
