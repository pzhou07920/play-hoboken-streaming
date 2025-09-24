import logger
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import yaml
import streaming_functions as sf
import google_auth as ga
from time import sleep
from contextlib import asynccontextmanager
import asyncio

ga.google_auth()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run at startup
    asyncio.create_task(sf.broadcast_monitor())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/stream", response_class=HTMLResponse)
async def stream(stream_name: str = Query(None)):
    # read in secrets.yml
    with open("secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)

    stream_name = stream_name.lower().capitalize()
    logger.log("capitalized stream_name " + stream_name)

    ga.google_auth()

    if sf.at_broadcast_limit(secrets['broadcast_limit']):
        return f"At broadcast limit of {secrets['broadcast_limit']}. Cannot start new broadcast."

    # check if stream is already running
    if not sf.broadcast_exists(stream_name):
        broadcast_id, stream_key = sf.create_broadcast(stream_name)
    else:
        broadcast_id = sf.get_running_broadcast(stream_name)
    
    if not sf.ffmpeg_running(stream_name):
        broadcast_id = sf.start_ffmpeg(stream_name, broadcast_id, stream_key, secrets)
    else:
        return f"Stream {stream_name} is already running. Watch the stream here: https://www.youtube.com/live/{broadcast_id}"
    
    return f"Stream has been started! Watch the stream here: <a href='https://www.youtube.com/live/{broadcast_id}'>Broadcast Link</a>"


@app.get("/test_multi_streams")
async def test_multi_streams(stream_count: int = Query(None)):
    # read in secrets.yml
    with open("secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)

    ga.google_auth()
    logger.log(f"Testing {stream_count} streams")
    count = 0
    for stream_name in secrets['stream_names']:
        if count < stream_count:
            logger.log(f"Starting stream: {stream_name}")
            broadcast_id = sf.start_ffmpeg(stream_name, secrets)
            count += 1
            sleep(20)
    logger.log(f"Stream has been started! Watch the stream here: https://www.youtube.com/live/{broadcast_id}")
    return "Multi-stream test completed."