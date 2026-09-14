"""Offline, packaged JSON Schema validation shared by CLI and HTTP paths."""
from functools import lru_cache
from importlib.resources import files
import json

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .errors import ContractError


@lru_cache(maxsize=8)
def validator(name):
    root = files('eju_bank').joinpath('schemas')
    schemas = {p.name: json.loads(p.read_text(encoding='utf-8')) for p in root.iterdir() if p.name.endswith('.json')}
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas.values())
    schema_key = name if name.endswith('.schema.json') else (name + '.schema.json')
    schema = schemas[schema_key]
    Draft202012Validator.check_schema(schema)
    # Registry has no retrieval callback: validation never downloads an external schema.
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def schema_issues(name, value):
    result = []
    stack=[(value,0)];count=0
    while stack:
        node,depth=stack.pop();count+=1
        if depth>48 or count>100000:
            return [{'code':'schema.complexity','message':'Content exceeds depth or node limit','ref':'$'}]
        if isinstance(node,dict): stack.extend((v,depth+1) for v in node.values())
        elif isinstance(node,list): stack.extend((v,depth+1) for v in node)
    for error in validator(name).iter_errors(value):
        # Do not echo source text, essays or secrets in a validation message.
        path = '/'.join(str(p) for p in error.absolute_path) or '$'
        result.append({'code': 'schema.' + error.validator, 'message': f'{path}: violates {error.validator}', 'ref': path})
        if len(result) >= 100:
            break
    return result


def require_schema(name, value):
    problems = schema_issues(name, value)
    if problems:
        raise ContractError('; '.join(p['message'] for p in problems[:8]))
