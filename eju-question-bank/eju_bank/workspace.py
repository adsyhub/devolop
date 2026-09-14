"""Resolve data roots independently of the installed package and current directory."""
from dataclasses import dataclass
from pathlib import Path
from .util import load_json
from .errors import ContractError

@dataclass(frozen=True)
class WorkspaceConfig:
    root: Path
    database: Path
    media: Path
    inventory: Path

    @classmethod
    def resolve(cls,*,root=None,config=None,database=None,media=None,inventory=None):
        data={};base=Path.cwd()
        if config:
            path=Path(config).expanduser().resolve();data=load_json(path);base=path.parent
            if not isinstance(data,dict) or set(data)-{'workspace','database','media','inventory'}:raise ContractError('Invalid workspace configuration')
        def relative(value,parent):
            p=Path(value).expanduser();return (p if p.is_absolute() else parent/p).resolve()
        inferred=Path(database).parent if database and Path(database).is_absolute() else base
        if inferred.name=='library':inferred=inferred.parent
        workspace=relative(root or data.get('workspace',str(inferred) if not config else '.'),base)
        db=relative(database or data.get('database','library/eju.db'),workspace)
        return cls(workspace,db,relative(media or data.get('media',str(db.parent/'media')),workspace),relative(inventory or data.get('inventory','content/content-inventory.json'),workspace))
