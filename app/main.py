import io
import zipfile
from pathlib import Path
from typing import Union

import builder
import uvicorn
from builder import Result
from fastapi import FastAPI, Response
from pydantic import BaseModel

app = FastAPI()


class buildRequest(BaseModel):
    keymap: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


def build_sample():
    path = Path(__file__).parent / "work" / "fish.keymap"
    result = builder.build_from_path(path)
    return tozip(result)


def tozip(result: Result):
    if result.result:
        responce = Response(
            result.data["zip"],
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment;filename={'fish.zip'}"},
        )
        return responce
    else:
        return {"msg": "build error"}


@app.get("/test_get")
def test_get():
    return build_sample()


@app.post("/test_post")
def test_post():
    return build_sample()


@app.post("/build")
def build(build_request: buildRequest):
    result = builder.build(keymap=build_request.keymap)
    return tozip(result)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
