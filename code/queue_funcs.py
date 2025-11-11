import logger
import os
import yaml
import asyncio
import pandas as pd
import streaming_functions as sf
from queue import Queue

def update_workflow_status(stream_name: str, is_running: bool):
    logger.log(f"Updating workflow status for {stream_name} to {is_running}")
    if os.path.exists('db/workflow_db.csv'):
        df = pd.read_csv('db/workflow_db.csv')
        if stream_name in df['stream_name'].values:
            df.loc[df['stream_name'] == stream_name, 'is_running?'] = 1 if is_running else 0
        else:
            new_row = pd.DataFrame([(stream_name, 1 if is_running else 0)], columns=['stream_name', 'is_running?'])
            df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv('db/workflow_db.csv', index=False)
    else:
        with open('db/workflow_db.csv', 'x', newline='') as csvfile:
            writer = pd.DataFrame(columns=['stream_name', 'is_running?'])
            writer.to_csv(csvfile, index=False)


def workflow_is_running(stream_name: str):
    if os.path.exists('db/workflow_db.csv'):
        df = pd.read_csv('db/workflow_db.csv')
        if stream_name in df['stream_name'].values:
            if df.loc[df['stream_name'] == stream_name, 'is_running?'].values[0] == 1:
                logger.log(f"Workflow for stream: {stream_name} is already running.")
                return
    else:
        with open('db/workflow_db.csv', 'x', newline='') as csvfile:
            writer = pd.DataFrame(columns=['stream_name', 'is_running?'])
            writer.to_csv(csvfile, index=False)

'''
Main function where the work happens. Creates the broadcast, creates the stream, starts ffmpeg, updates nginx, and reloads nginx.
'''
def start_workflow(nginx_path: str, stream_name:str, secrets: dict):
    update_workflow_status(stream_name, True)

    if not sf.stream_is_live(stream_name):
        logger.log(f"Stream {stream_name} is not live. Starting new broadcast and ffmpeg process.")
        broadcast_id, stream_id, stream_key = sf.create_broadcast(stream_name)
        sf.update_nginx_stream_urls(nginx_path, stream_name, broadcast_id)
        broadcast_id = sf.start_ffmpeg(stream_name, broadcast_id, stream_id, stream_key, secrets)
        logger.log(f"Stream {stream_name} has been started!")
    
    update_workflow_status(stream_name, False)

async def queue_monitor(queue: Queue):
    while True:
        await asyncio.sleep(2)
        if not queue.empty():
            stream_name = queue.get()
            if workflow_is_running(stream_name):
                logger.log(f"Workflow for stream: {stream_name} is already running. Skipping.")
                continue
            logger.log(f"Starting workflow for stream: {stream_name}")
            # read in secrets.yml
            with open("config/secrets.yml", "r") as f:
                secrets = yaml.safe_load(f)
            start_workflow(secrets['nginx_path'], stream_name, secrets)