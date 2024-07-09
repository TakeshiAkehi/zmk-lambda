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


def docker_push_fishfile(container_name, src, dstname):
    return run_on_shell(f"docker cp {src} {container_name}:/zmk-firmware/config/boards/shields/fish/{dstname}")


def docker_pull_uf2(container_name, dstpath, side: Side):
    return run_on_shell(
        f"docker cp {container_name}:/zmk-firmware/build/fish_{side.value}/zephyr/zmk.uf2 {str(dstpath)}"
    )


def docker_clean(container_name):
    return run_on_shell(f"docker exec {container_name} rm /zmk-firmware/build/* -rf")


def docker_check_if_running(container_name):
    s = run_on_shell(f"docker ps -q -f name={container_name}")
    ret = (len(s) == 2) and (len(s[0]) == 12) and s[1] == ""
    return ret


class buildContainer:
    def __init__(self, keymap: str, side: Side, conf: str = None, defconfig: str = None):
        self.keymap = keymap
        self.side = side
        self.container_name = f"zmk-{randomname(16)}"
        self.workdir = BUILD_DIR / self.container_name
        self.IMAGE_NAME = IMAGE_NAME_LEFT if side == Side.left else IMAGE_NAME_RIGHT
        self.conf = conf
        self.defconfig = defconfig

    def __enter__(self):
        os.makedirs(self.workdir)
        open_on_shell(f"docker run --rm --name {self.container_name} {self.IMAGE_NAME} tail -F /dev/null")
        return self

    def exec_build(self):
        container_name = self.container_name
        side = self.side

        LOGGER.info(f"building on container_name={self.container_name}")
        if not wait_until(lambda: docker_check_if_running(container_name=container_name), timeout=10):
            return Result(False, "timeout to container up", None)

        keymap_file = self.workdir / "fish.keymap"
        with open(keymap_file, "w") as f:
            f.write(self.keymap)
        docker_push_keymap(container_name=container_name, src=str(keymap_file))

        if self.conf is not None:
            conf_file = self.workdir / "fish.conf"
            with open(conf_file, "w") as f:
                f.write(self.conf)
            docker_push_fishfile(container_name=container_name, src=str(conf_file), dstname="fish.conf")

        if self.defconfig is not None:
            defconf_file = self.workdir / "Kconfig.defconfig"
            with open(defconf_file, "w") as f:
                f.write(self.defconfig)
            docker_push_fishfile(container_name=container_name, src=str(defconf_file), dstname="Kconfig.defconfig")

        prinstine_build = self.conf is not None or self.defconfig is not None
        optarg = "-p" if prinstine_build else ""
        build_log = run_on_shell(f"docker exec {container_name} /bin/bash build_uf2.sh {side.value} {optarg}")
        LOGGER.info(build_log)
        uf2_path = self.workdir / f"{side.value}.uf2"
        docker_pull_uf2(container_name=container_name, dstpath=str(uf2_path), side=self.side)

        # load on memory
        if not Path(uf2_path).exists():
            return Result(True, "build failed", {"log": build_log})

        with open(uf2_path, "rb") as f:
            uf2_object = io.BytesIO(f.read())
        return Result(True, "build succeed", {"uf2": uf2_object, "log": build_log})

    def __exit__(self, exception_type, exception_value, traceback):
        # pass
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
            zf.writestr(zinfo_or_arcname=zb.path, data=zb.data)
    return zf, s


def build(keymap: str, defconfig=None, conf=None):
    with buildContainer(keymap=keymap, side=Side.left, conf=conf, defconfig=defconfig) as container:
        res1 = container.exec_build()
        LOGGER.info(res1.msg)
    with buildContainer(keymap=keymap, side=Side.right, conf=conf, defconfig=defconfig) as container:
        res2 = container.exec_build()
        LOGGER.info(res2.msg)

    zipbytes_list = [ZipBytes(bytes(keymap, "utf8"), "fish.keymap")]
    if res1.data is not None:
        if "uf2" in res1.data.keys():
            zipbytes_list.append(ZipBytes(res1.data["uf2"].getbuffer(), "left.uf2"))
        if "log" in res1.data.keys():
            zipbytes_list.append(ZipBytes(bytes("\n".join(res1.data["log"]), "utf8"), "build_log_left.txt"))
    if res2.data is not None:
        if "uf2" in res2.data.keys():
            zipbytes_list.append(ZipBytes(res2.data["uf2"].getbuffer(), "right.uf2"))
        if "log" in res2.data.keys():
            zipbytes_list.append(ZipBytes(bytes("\n".join(res2.data["log"]), "utf8"), "build_log_right.txt"))
    if defconfig is not None:
        zipbytes_list.append(ZipBytes(bytes(defconfig, "utf8"), "Kconfig.defconfig"))
    if conf is not None:
        zipbytes_list.append(ZipBytes(bytes(conf, "utf8"), "fish.conf"))

    zf, s = zipdata(zipbytes_list)

    if not res1.result or not res2.result:
        return Result(False, "build failed", {"zip": s.getvalue()})
    else:
        return Result(True, "build success", {"zip": s.getvalue()})


def build_from_path(keymap_file: Path):
    with open(keymap_file) as f:
        keymap = f.read()
    return build(keymap)


def build_from_path_with_option(keymap_file: Path, defconfig_file: Path = None, conf_file: Path = None):
    with open(keymap_file) as f:
        keymap = f.read()
    if conf_file is not None:
        with open(conf_file) as f:
            conf = f.read()
    else:
        conf = None
    if defconfig_file is not None:
        with open(defconfig_file) as f:
            defconf = f.read()
    else:
        defconf = None

    return build(keymap, defconf, conf)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    WDIR = CDIR / "work"
    res = build_from_path(WDIR / "keymap3.keymap")
    # res = build_from_path_with_option(WDIR / "keymap2.keymap", WDIR / "KconfigL.defconfig", WDIR / "conf2.conf")
    with open("export/test.zip", "wb") as f:
        f.write(res.data["zip"])
    shutil.unpack_archive("export/test.zip", "export/")
