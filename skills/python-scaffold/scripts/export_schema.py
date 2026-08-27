import json
from pathlib import Path

from python_scaffold.models import Profile

ROOT = Path(__file__).resolve().parents[1]
schema = json.dumps(Profile.model_json_schema(), indent=2, sort_keys=True) + "\n"
(ROOT / "src/python_scaffold/config/schema.json").write_text(schema)
