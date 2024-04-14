import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.append("/zmk-firmware")
import build_fish


def res(body_dict):
    return {
        # 'isBase64Encoded': False,
        "statusCode": 200,
        # 'headers': {},
        "body": json.dumps(body_dict),
    }


def replace_nums(inputstr: str):
    ret = (
        inputstr.replace("-", "")
        .replace("0", "g")
        .replace("1", "h")
        .replace("2", "i")
        .replace("3", "j")
        .replace("4", "k")
        .replace("5", "l")
        .replace("6", "m")
        .replace("7", "n")
        .replace("8", "o")
        .replace("9", "p")
    )
    return ret


def handler(event, context):
    p = subprocess.run("west help", stdout=subprocess.PIPE, shell=True)
    west_str = p.stdout.decode("utf8").replace("\n", "")
    if event is None or "userid" not in event:
        ret = {"msg": "Hello from AWS Lambda using Python %s, %s\n%s" % (sys.version, west_str, context.aws_request_id)}
        return res(ret)

    if event["userid"] == "random":
        shield = replace_nums(context.aws_request_id)
    else:
        shield = replace_nums(event["userid"])

    if not Path("/tmp/zmk-firmware").exists():
        shutil.copytree("/zmk-firmware", "/tmp/zmk-firmware", dirs_exist_ok=True)
    ret = build_fish.main(shield)

    return res(ret)
