import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

# ZMKROOT = Path(__file__).parent
ZMKROOT = Path("/zmk-firmware")


def create_shield_config(template_dir: Path, shields_dir: Path, shield: str):
    shield_lower = shield.lower()
    shield_upper = shield.upper()
    new_config_dir = Path("/tmp/config")
    new_shield_dir = new_config_dir / "boards" / "shields" / shield_lower
    # new_shield_dir = shields_dir / shield_lower #
    new_shield_dir.mkdir(parents=True, exist_ok=True)
    for file in template_dir.glob("*"):
        dst = new_shield_dir / file.name.replace("template", shield_lower)
        print("%s -> %s" % (file, dst))
        with open(file, "r") as f:
            template_str = f.read()
        new_file_str = template_str.replace("$template$", shield_lower).replace("$TEMPLATE$", shield_upper)
        with open(dst, "w") as f:
            f.write(new_file_str)
    return new_config_dir


def exec_build(appdir, board, confdir, build_dir, shield):
    cmd_list = ["west", "build", "-p"]
    cmd_list += ["-s", appdir]
    cmd_list += ["-b", board]
    cmd_list += ["-d", build_dir]
    cmd_list += ["--"]
    cmd_list += ["-DSHIELD=%s" % (shield)]
    cmd_list += ["-DZMK_CONFIG=%s" % (confdir)]
    cmd = " ".join([str(c) for c in cmd_list])
    build_dir.mkdir(exist_ok=True, parents=True)
    print(cmd)

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=ZMKROOT)
    stdout_str = p.stdout.decode("utf-8")
    firmware_path = build_dir / "zephyr" / "zmk.uf2"
    ok = firmware_path.exists()
    ret = {"ok": ok, "path": firmware_path, "stdout": stdout_str}
    return ret


def exec_build_lr(appdir, board, build_dir, shield, confdir):
    shield_left = shield + "_left"
    build_dir_left = build_dir / shield_left
    left = exec_build(appdir=appdir, board=board, confdir=confdir, build_dir=build_dir_left, shield=shield_left)

    shield_right = shield + "_right"
    build_dir_right = build_dir / shield_right
    right = exec_build(appdir=appdir, board=board, confdir=confdir, build_dir=build_dir_right, shield=shield_right)

    ret = {"left": left, "right": right}
    return ret


def main(shield: str, file: Path = None):
    CONFIG_DIR = ZMKROOT / "config"
    SHIELDS_DIR = CONFIG_DIR / "boards" / "shields"
    TEMPLATE_DIR = SHIELDS_DIR / "template"
    # BUILD_DIR = ZMKROOT / "build"
    BUILD_DIR = Path("/tmp") / "build"
    APP_DIR = ZMKROOT / "zmk" / "app"
    BOARD = "seeeduino_xiao_ble"

    tmp_config_dir = create_shield_config(template_dir=TEMPLATE_DIR, shields_dir=SHIELDS_DIR, shield=shield)
    ret = exec_build_lr(appdir=APP_DIR, board=BOARD, confdir=tmp_config_dir, build_dir=BUILD_DIR, shield=shield)
    # ret = exec_build_lr(appdir=APP_DIR, board=BOARD, confdir=CONFIG_DIR, build_dir=BUILD_DIR, shield=shield)
    print(ret)
    if file is not None:
        with open(file, "w") as f:
            f.write(str(ret))


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("shield")
    parser.add_argument("--file", type=Path)
    parsed_args = parser.parse_args()
    ret = {"shield": parsed_args.shield, "file": parsed_args.file}
    return ret


if __name__ == "__main__":
    main(**handle_args())
