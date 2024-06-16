import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

# ZMKROOT = Path(__file__).parent
ZMKROOT = Path("/zmk-firmware")
# ZMKROOT = Path("/tmp/zmk-firmware")


def create_shield_config(template_dir: Path, shields_dir: Path, shield: str):
    print("creating shield config : template_dir=%s -> shields_dir=%s, shield=%s" % (template_dir, shields_dir, shield))
    shield_lower = shield.lower()
    shield_upper = shield.upper()
    new_shield_dir = shields_dir / shield_lower
    print("new shield dir = %s" % new_shield_dir)
    new_shield_dir.mkdir(parents=True, exist_ok=True)

    dbgcnt = 0
    for file in template_dir.glob("*"):
        dst = new_shield_dir / file.name.replace("template", shield_lower)
        if dst.exists() and dst.suffix != ".keymap":
            print("copying %s skipped : already exists %s" % (file, dst))
            continue

        print("%s -> %s" % (file, dst))
        with open(file, "r") as f:
            template_str = f.read()
        new_file_str = template_str.replace("$template$", shield_lower).replace("$TEMPLATE$", shield_upper)
        with open(dst, "w") as f:
            f.write(new_file_str)
        dbgcnt += 1
    print("# of created fileds = %d" % dbgcnt)
    return shield_lower


def exec_build(appdir: Path, board: str, confdir: Path, build_dir: Path, shield: str):
    print("config list in %s:" % confdir)
    print("%s" % list(confdir.glob("**/*")))
    # for file in confdir.glob("**/*"):
    #     if not file.is_dir():
    #         print("==========")
    #         print(">> %s" % file)
    #         with open(file) as f:
    #             lines = f.read().split("\n")
    #         print("\n".join(lines[0:10]))

    p = subprocess.run(
        "west zephyr-export",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        cwd=ZMKROOT,
        env=os.environ.copy(),
    )
    stdout_str = p.stdout.decode("utf-8")
    print(stdout_str)

    cmd_list = ["west", "build"]
    cmd_list += ["-s", appdir]
    cmd_list += ["-b", board]
    cmd_list += ["-d", build_dir]
    cmd_list += ["--"]
    cmd_list += ["-DSHIELD=%s" % (shield)]
    cmd_list += ["-DZMK_CONFIG=%s" % (confdir)]
    cmd = " ".join([str(c) for c in cmd_list])
    build_dir.mkdir(exist_ok=True, parents=True)
    print("cmd: ", cmd)
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        cwd=ZMKROOT,
        env=os.environ.copy(),
    )
    stdout_str = p.stdout.decode("utf-8")
    print(stdout_str)

    firmware_path = build_dir / "zephyr" / "zmk.uf2"
    ok = firmware_path.exists()
    ret = {"ok": ok, "path": str(firmware_path), "stdout": stdout_str}
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


def main(shield: str):
    # TMP_DIR = Path("/tmp")
    CONFIG_DIR = ZMKROOT / "config"
    SHIELDS_DIR = CONFIG_DIR / "boards" / "shields"
    BUILD_DIR = ZMKROOT / "build"

    TEMPLATE_DIR = ZMKROOT / "config" / "boards" / "shields" / "template"
    APP_DIR = ZMKROOT / "zmk" / "app"
    BOARD = "seeeduino_xiao_ble"

    shield_lower = create_shield_config(template_dir=TEMPLATE_DIR, shields_dir=SHIELDS_DIR, shield=shield)
    ret = exec_build_lr(appdir=APP_DIR, board=BOARD, confdir=CONFIG_DIR, build_dir=BUILD_DIR, shield=shield_lower)
    print(ret)
    return ret


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("shield")
    parsed_args = parser.parse_args()
    ret = {"shield": parsed_args.shield}
    return ret


if __name__ == "__main__":
    main(**handle_args())
