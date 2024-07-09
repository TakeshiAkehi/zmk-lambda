import json
from pathlib import Path


def create_json(keymap, conf=None, defconf=None):
    with open(keymap) as f:
        lines = f.read()
    j = {"keymap": lines}
    if conf is not None:
        with open(conf) as f:
            lines = f.read()
        j["conf"] = lines

    if defconf is not None:
        with open(defconf) as f:
            lines = f.read()
        j["defconfig"] = lines

    # jstr = json.dumps(j).replace("\\n", "\\n\n")

    with open(WDIR / "temp.json", "w") as f:
        json.dump(j, f)
    #     f.write(jstr)


WDIR = Path(__file__).parent / "work"
keymap = WDIR / "keymap3.keymap"
conf = WDIR / "conf2.conf"
defconf = WDIR / "Kconfig.defconfig"

create_json(keymap, conf, defconf)
