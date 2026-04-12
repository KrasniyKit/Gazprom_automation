import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
schema = json.loads((ROOT / "schemas" / "schema.json").read_text(encoding="utf-8"))

validator = Draft202012Validator(schema)

for sample in ["valid.json", "invalid.json"]:
    data = json.loads((ROOT / "samples" / sample).read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        print(f"Validation errors in {sample}:")
        for error in errors:
            print(f"- {error.message}")
    else:
        print(f"{sample} is valid.")