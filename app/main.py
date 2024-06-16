from pathlib import Path
from typing import Union

import builder
import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/test1")
def read_test():
    path = Path(__file__).parent / "work/fish.keymap"
    builder.build(path)
    return {"build": "1"}


@app.get("/test2")
def read_test():
    path = Path(__file__).parent / "work/fish2.keymap"
    builder.build(path)
    return {"build": "2"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
