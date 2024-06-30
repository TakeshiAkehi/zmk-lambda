import io
import logging
import os
import random
import shutil
import string
import subprocess
import time
import zipfile
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)
CDIR = Path(__file__).parent
BUILD_DIR = CDIR / "work"
IMAGE_NAME_LEFT = "zmk-api:left"
IMAGE_NAME_RIGHT = "zmk-api:right"


class Side(Enum):
    left = "left"
    right = "right"


@dataclass
class Result:
    result: bool
    msg: str
    data: object


# util
def run_on_shell(command):
    p = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return p.stdout.decode("utf-8").split("\n")


def open_on_shell(command):
    p = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return p


def randomname(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def wait_until(condition_func, timeout):
    loopcnt = 0
    while not condition_func():
        time.sleep(1)
        loopcnt += 1
        if loopcnt > timeout:
            return False
    return True


# docker func
def docker_cp(container_name, src, dst):
    return run_on_shell(f"docker cp {src} {container_name}:{dst}")


def docker_push_keymap(container_name, src):
    return run_on_shell(f"docker cp {src} {container_name}:/zmk-firmware/config/boards/shields/fish/fish.keymap")


def docker_pull_uf2(container_name, dstpath, side: Side):
    return run_on_shell(
        f"docker cp {container_name}:/zmk-firmware/build/fish_{side.value}/zephyr/zmk.uf2 {str(dstpath)}"
    )


def docker_check_if_running(container_name):
    s = run_on_shell(f"docker ps -q -f name={container_name}")
    ret = (len(s) == 2) and (len(s[0]) == 12) and s[1] == ""
    return ret


class buildContainer:
    def __init__(self, keymap: str, side: Side):
        self.keymap = keymap
        self.side = side
        self.container_name = f"zmk-{randomname(16)}"
        self.workdir = BUILD_DIR / self.container_name
        self.IMAGE_NAME = IMAGE_NAME_LEFT if side == Side.left else IMAGE_NAME_RIGHT

    def __enter__(self):
        os.makedirs(self.workdir)
        open_on_shell(f"docker run --rm --name {self.container_name} {self.IMAGE_NAME} tail -F /dev/null")
        return self

    def exec_build(self):
        container_name = self.container_name
        keymap_file = self.workdir / "fish.keymap"
        side = self.side

        with open(keymap_file, "w") as f:
            f.write(self.keymap)

        LOGGER.info(f"building on container_name={self.container_name}")
        if not wait_until(lambda: docker_check_if_running(container_name=container_name), timeout=10):
            return Result(False, "timeout to container up", None)

        docker_push_keymap(container_name=container_name, src=str(keymap_file))
        build_log = run_on_shell(f"docker exec {container_name} /bin/bash build_uf2.sh {side.value}")
        LOGGER.info(build_log)
        uf2_path = self.workdir / f"{side.value}.uf2"
        docker_pull_uf2(container_name=container_name, dstpath=str(uf2_path), side=self.side)

        # load on memory
        with open(uf2_path, "rb") as f:
            uf2_object = io.BytesIO(f.read())
        return Result(True, "built uf2", {"uf2": uf2_object, "log": build_log})

    def __exit__(self, exception_type, exception_value, traceback):
        shutil.rmtree(self.workdir)
        run_on_shell(f"docker stop {self.container_name}")


@dataclass
class ZipBytes:
    data: bytes
    path: str


def zipdata(zb_list=List[ZipBytes]):
    s = io.BytesIO()
    with zipfile.ZipFile(s, "w") as zf:
        for zb in zb_list:
            zf.writestr(zinfo_or_arcname=zb.path, data=zb.data.getbuffer())
    return zf, s


def build(keymap: str):
    with buildContainer(keymap=keymap, side=Side.left) as container:
        res1 = container.exec_build()
        LOGGER.info(res1.msg)
    with buildContainer(keymap=keymap, side=Side.right) as container:
        res2 = container.exec_build()
        LOGGER.info(res2.msg)
    if not res1.result or not res2.result:
        return Result(False, "build failed", None)

    zf, s = zipdata([ZipBytes(res1.data["uf2"], "left.uf2"), ZipBytes(res2.data["uf2"], "right.uf2")])
    return Result(True, "build success", {"zip": s.getvalue()})


def build_from_path(keymap_file: Path):
    with open(keymap_file) as f:
        keymap = f.read()
    return build(keymap)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    res = build_from_path(CDIR / "work" / "fish.keymap")
    with open("test.zip", "wb") as f:
        f.write(res.data["zip"])
    a = 1
