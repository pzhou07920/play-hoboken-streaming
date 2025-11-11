import logger
import asyncio
import yaml
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import streaming_functions as sf
import google_auth as ga
from time import sleep
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from queue import Queue
from queue_funcs import queue_monitor
from startup_funcs import startup_db_setup, startup_wf_setup

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run at startup
    startup_db_setup()
    startup_wf_setup()
    asyncio.create_task(queue_monitor(workflow_queue))
    # Start the broadcast monitor in the background
    # This function closes streams that are not being watched
    asyncio.create_task(sf.broadcast_monitor())
    yield

ga.google_auth()
app = FastAPI(lifespan=lifespan)
workflow_queue = Queue()

origins = [
    "https://stream.playhoboken.com",  # WordPress website
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # allowed domains
    allow_credentials=True,
    allow_methods=["*"],               # or limit: ["GET", "POST"]
    allow_headers=["*"],               # or specify: ["Content-Type", "Authorization"]
)

@app.get("/stream", response_class=HTMLResponse)
async def stream(stream_name: str = Query(None)):
    # read in secrets.yml
    with open("config/secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)

    stream_name = stream_name.lower()
    if stream_name not in secrets['camera_stream_mapping']:
        return f"Invalid stream_name query parameter. Query parameter {stream_name} was passed"

    # ga.google_auth()

    workflow_queue.put(stream_name)
    # check if stream is already running
    if not sf.stream_is_live(stream_name):
        return f"Stream {stream_name} is starting!"

    return f"Stream {stream_name} is already live!"

# To allow the initial CORS OPTIONS call to succeed
# This is required to allow cross-origin requests from the WordPress site
@app.options('/stream', response_class=HTMLResponse)
async def stream_options():
    return None

# Testing endpoint
@app.get("/test_multi_streams")
async def test_multi_streams(stream_count: int = Query(None)):
    # read in secrets.yml
    with open("config/secrets.yml", "r") as f:
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