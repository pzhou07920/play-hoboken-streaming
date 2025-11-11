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
from queue import Queue

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
        if ga.get_broadcast_status(broadcast_id) != 'live':
            logger.log(f'Broadcast ID: {broadcast_id} is not live. Removing from broadcast_db.csv')
            broadcast_df = broadcast_df[broadcast_df['broadcast_id'] != broadcast_id]
        else:
            # kill the ffmpeg process
            pid = row['pid']
            if pid != '':
                try:
                    logger.log(f'Killing ffmpeg process with PID: {pid}')
                    os.kill(pid, 9)
                except Exception as e:
                    logger.log(f'Error killing ffmpeg process with PID: {pid} | Error: {e}')
            # terminate the broadcast
            ga.terminate_broadcast(broadcast_id)
    broadcast_df.to_csv('broadcast_db.csv', index=False)

def workflow_is_running(stream_name: str):
    if os.path.exists('workflow_db.csv'):
        df = pd.read_csv('workflow_db.csv')
        if stream_name in df['stream_name'].values:
            if df.loc[df['stream_name'] == stream_name, 'is_running?'].values[0] == 1:
                logger.log(f"Workflow for stream: {stream_name} is already running.")
                return
    else:
        with open('workflow_db.csv', 'x', newline='') as csvfile:
            writer = pd.DataFrame(columns=['stream_name', 'is_running?'])
            writer.to_csv(csvfile, index=False)

def startup_wf_setup():
    # Create fresh workflow_db.csv since Queue is empty on startup
    if os.path.exists('workflow_db.csv'):
        os.remove('workflow_db.csv')
    with open('workflow_db.csv', 'x', newline='') as csvfile:
        writer = pd.DataFrame(columns=['stream_name', 'is_running?'])
        writer.to_csv(csvfile, index=False)

def update_workflow_status(stream_name: str, is_running: bool):
    logger.log(f"Updating workflow status for {stream_name} to {is_running}")
    if os.path.exists('workflow_db.csv'):
        df = pd.read_csv('workflow_db.csv')
        if stream_name in df['stream_name'].values:
            df.loc[df['stream_name'] == stream_name, 'is_running?'] = 1 if is_running else 0
        else:
            new_row = pd.DataFrame([(stream_name, 1 if is_running else 0)], columns=['stream_name', 'is_running?'])
            df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv('workflow_db.csv', index=False)
    else:
        with open('workflow_db.csv', 'x', newline='') as csvfile:
            writer = pd.DataFrame(columns=['stream_name', 'is_running?'])
            writer.to_csv(csvfile, index=False)

def start_workflow(nginx_path: str, stream_name:str, secrets: dict):
    update_workflow_status(stream_name, True)

    if not sf.stream_is_live(stream_name):
        logger.log(f"Stream {stream_name} is not live. Starting new broadcast and ffmpeg process.")
        broadcast_id, stream_id, stream_key = sf.create_broadcast(stream_name)
        broadcast_id = sf.start_ffmpeg(stream_name, broadcast_id, stream_id, stream_key, secrets)
        sf.update_nginx_stream_urls(nginx_path, stream_name, broadcast_id)
        sf.reload_nginx(nginx_path)
        logger.log(f"Stream {stream_name} has been started!")
    
    update_workflow_status(stream_name, False)

async def queue_monitor():
    while True:
        await asyncio.sleep(2)
        if not workflow_queue.empty():
            stream_name = workflow_queue.get()
            if workflow_is_running(stream_name):
                logger.log(f"Workflow for stream: {stream_name} is already running. Skipping.")
                continue
            logger.log(f"Starting workflow for stream: {stream_name}")
            # read in secrets.yml
            with open("config/secrets.yml", "r") as f:
                secrets = yaml.safe_load(f)
            start_workflow(secrets['nginx_path'], stream_name, secrets)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run at startup
    startup_db_setup()
    startup_wf_setup()
    asyncio.create_task(queue_monitor())
    # Start the broadcast monitor in the background
    # This function closes streams that are not being watched
    asyncio.create_task(sf.broadcast_monitor())
    yield

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

    ga.google_auth()

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