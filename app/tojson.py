import json
from pathlib import Path

path = Path("/home/ake/soft/zmk-lambda/app/work/fish3.keymap")
with open(path) as f:
    lines = f.read()

j = {"keymap": lines}

with open(path.with_suffix(".json"), "w") as f:
    json.dump(j, f)
