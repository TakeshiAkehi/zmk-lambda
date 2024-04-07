import json
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


def handler(event, context):
    p = subprocess.run("west --version", stdout=subprocess.PIPE, shell=True)
    west_version = p.stdout.decode("utf8").replace("\n", "")
    if event is None or "mode" not in event:
        ret = {
            "msg": "Hello from AWS Lambda using Python %s, %s\n%s" % (sys.version, west_version, context.aws_request_id)
        }
        return res(ret)

    random_name = (
        context.aws_request_id.replace("-", "")
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
    shield = "fish_%s" % random_name
    ret = build_fish.main(shield)
    return res(ret)
