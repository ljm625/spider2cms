import uvicorn
from typing import Union
import sqlite3

from fastapi import FastAPI
from sites.jable import Jable
app = FastAPI()
db = sqlite3.connect("data.db")
jabel = Jable("https://jable.tv",db)
@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/provide/vod/")
async def serve(ac: Union[str, None] = None, ids: Union[int, None] = None,pg: Union[int, None] = None,wd: Union[str, None] = None):
    await jabel.get_class()
    return {"ac": ac, "ids": ids,"pg":pg, "wd":wd}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
