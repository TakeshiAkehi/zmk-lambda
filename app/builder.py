import os
import random
import shutil
import string
import subprocess
from pathlib import Path

IMAGE_NAME = "zmk-api:latest"
CDIR = Path(__file__).parent
BUILD_DIR = CDIR / "work"


def randomname(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def build(keymap_file):
    container = f"zmk-{randomname(16)}"
    workdir = BUILD_DIR / container
    os.makedirs(workdir)

    print(f"building on container {container}")
    pc = subprocess.Popen(f"docker run --rm --name {container} {IMAGE_NAME} tail -F /dev/null", shell=True)
    pc_tx = subprocess.run(
        f"docker cp {str(keymap_file)} {container}:/zmk-firmware/config/boards/shields/fish/fish.keymap", shell=True
    )

    print(f"building left...")
    pc_l = subprocess.run(
        f"docker exec {container} /bin/bash build_uf2.sh left",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(pc_l.stdout.decode())
    subprocess.run(
        f"docker cp {container}:/zmk-firmware/build/fish_left/zephyr/zmk.uf2 {str(workdir)}/fish_left.uf2", shell=True
    )

    print(f"building right...")
    pc_r = subprocess.run(
        f"docker exec {container} /bin/bash build_uf2.sh right",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(pc_r.stdout.decode())
    subprocess.run(
        f"docker cp {container}:/zmk-firmware/build/fish_right/zephyr/zmk.uf2 {str(workdir)}/fish_right.uf2", shell=True
    )
    subprocess.run(f"docker rm -f {container}", shell=True)


if __name__ == "__main__":
    build(CDIR / "work" / "fish.keymap")
    build(CDIR / "work" / "fish2.keymap")
