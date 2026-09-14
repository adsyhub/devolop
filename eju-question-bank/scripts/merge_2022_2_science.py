#!/usr/bin/env python3
"""Merge 2022-2 Physics, Chemistry, and Biology explanations into work/2022-2-science/explanations.json."""

import json
from pathlib import Path

science_dir = Path("work/2022-2-science")

phys_file = science_dir / "physics_explanations.json"
chem_file = science_dir / "chemistry_explanations.json"
bio_file = science_dir / "biology_explanations.json"

phys_data = json.loads(phys_file.read_text(encoding="utf-8"))
chem_data = json.loads(chem_file.read_text(encoding="utf-8"))
bio_data = json.loads(bio_file.read_text(encoding="utf-8"))

science_explanations = {
    "session": "2022-2",
    "subject": "SCIENCE",
    "forms": {
        "PHYSICS_JA": phys_data,
        "CHEMISTRY_JA": chem_data,
        "BIOLOGY_JA": bio_data,
    }
}

out_file = science_dir / "explanations.json"
out_file.write_text(json.dumps(science_explanations, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Successfully merged 2022-2 Science explanations into {out_file}:")
print(f"  PHYSICS_JA  : {len(phys_data)} questions")
print(f"  CHEMISTRY_JA: {len(chem_data)} questions")
print(f"  BIOLOGY_JA  : {len(bio_data)} questions")
print(f"  Total       : {len(phys_data) + len(chem_data) + len(bio_data)} questions")

