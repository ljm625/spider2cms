import uvicorn
from typing import Union
import sqlite3

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sites.jable import Jable
from sites.fourkav import FourKAV
import os

host_url = "http://127.0.0.1:8000"
if os.environ.get('HOST_URL'):
    host_url = os.environ["HOST_URL"]
app = FastAPI()
db = sqlite3.connect("data.db")
jabel = Jable("https://jable.tv",db)
fourkav = FourKAV("https://4k-av.com",f"{host_url}/4kav/vod/",db)
@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/4kav/vod/")
async def serve(ac: Union[str, None] = None, ids: Union[int, None] = None,t: Union[int,str, None] = None,pg: Union[int, None] = None,wd: Union[str, None] = None,url: Union[str, None] = None):
    if ac is None or ac=="list":
        return await fourkav.get_class()
    if ac=="detail":
        if ids:
            return await fourkav.get_video(ids)
        elif wd:
            return await fourkav.search_video(wd,pg)
        else:
            return await fourkav.get_videos_by_class(t,pg)
    if ac=="play":
        data = await fourkav.get_video_play_url(url)
        return RedirectResponse(data["data"],302)

    return {"code":0}


@app.get("/jable/vod/")
async def serve(ac: Union[str, None] = None, ids: Union[int, None] = None,t: Union[int,str, None] = None,pg: Union[int, None] = None,wd: Union[str, None] = None):
    if ac is None or ac=="list":
        return await jabel.get_class()
    if ac=="detail":
        if ids:
            return await jabel.get_video(ids)
        elif wd:
            return await jabel.search_video(wd,pg)
        else:
            return await jabel.get_videos_by_class(t,pg)
    return {"code":0}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
