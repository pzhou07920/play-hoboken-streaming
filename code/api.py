import logger
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import yaml
import streaming_functions as sf
import google_auth as ga
from time import sleep
from contextlib import asynccontextmanager
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

ga.google_auth()

def startup_db_setup():
    # check if broadcast_db.csv exists, if not create it and add header
    if os.path.exists('broadcast_db.csv'):
        logger.log("broadcast_db.csv exists!")
    else:
        with open('broadcast_db.csv', 'x', newline='') as csvfile:
            writer = pd.DataFrame(columns=['stream_name', 'pid', 'broadcast_id'])
            writer.to_csv(csvfile, index=False)
            
    broadcast_df = pd.read_csv('broadcast_db.csv')
    for index, row in broadcast_df.iterrows():
        broadcast_id = row['broadcast_id']
        if not ga.broadcast_is_live(broadcast_id):
            logger.log(f'Broadcast ID: {broadcast_id} is not live. Removing from broadcast_db.csv')
            broadcast_df = broadcast_df[broadcast_df['broadcast_id'] != broadcast_id]
            # kill the ffmpeg process
            pid = row['pid']
            if pid != '':
                try:
                    logger.log(f'Killing ffmpeg process with PID: {pid}')
                    os.kill(pid, 9)
                except Exception as e:
                    logger.log(f'Error killing ffmpeg process with PID: {pid} | Error: {e}')
    broadcast_df.to_csv('broadcast_db.csv', index=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run at startup
    startup_db_setup()
    # Start the broadcast monitor in the background
    # This function closes streams that are not being watched
    asyncio.create_task(sf.broadcast_monitor())
    yield

app = FastAPI(lifespan=lifespan)

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
        return f"Invalid stream_name query parameter. Query parameter ${stream_name} was passed"

    ga.google_auth()

    # check if stream is already running
    if not sf.stream_is_live(stream_name):
        nginx_path = secrets['nginx_path']
        broadcast_id, stream_key = sf.create_broadcast(stream_name)
        broadcast_id = sf.start_ffmpeg(stream_name, broadcast_id, stream_key, secrets)
        sf.update_nginx_stream_urls(nginx_path, stream_name, broadcast_id)
        sf.reload_nginx(nginx_path)

    return f"Stream ${stream_name} is already live!"

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