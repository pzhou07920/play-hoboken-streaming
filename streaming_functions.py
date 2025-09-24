import logger
from time import sleep
import google_auth as ga
import subprocess
import csv
import os
import pandas as pd
import asyncio

def at_broadcast_limit(broadcast_limit: int):
    # check if stream_pid_logger.csv exists, if not create it and add header
    if os.path.exists('stream_pid_logger.csv'):
        logger.log("stream_pid_logger.csv exists!")
    else:
        with open('stream_pid_logger.csv', 'x', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['stream_name', 'pid', 'broadcast_id'])

    with open('stream_pid_logger.csv', 'r', newline='') as csvfile:
        #csvfile.seek(0)
        reader = csv.reader(csvfile)
        # count the number of rows in the csv file
        row_count = sum(1 for row in reader) - 1  # subtract 1 for header
        logger.log(f"Current number of broadcasts: {row_count}")
        if row_count >= broadcast_limit:
            logger.log(f"At broadcast limit of {broadcast_limit}. Cannot start new broadcast.")
            return True
        else:
            return False

def broadcast_exists(stream_name: str):
    with open('stream_pid_logger.csv', 'r', newline='') as csvfile:
        # Check if the stream_name already exists in the csv file
        #csvfile.seek(0)
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == stream_name:
                logger.log(f"Stream {row[0]} with PID {row[1]} and Broadcast ID {row[2]} already exists.")
                return True
    return False

def get_running_broadcast(stream_name: str):
    if os.path.exists('stream_pid_logger.csv'):
        with open('stream_pid_logger.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                if row[0] == stream_name:
                    broadcast_id = row[2]
                    return broadcast_id
    return None

def ffmpeg_running(stream_name: str):
    if os.path.exists('stream_pid_logger.csv'):
        with open('stream_pid_logger.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                if row[0] == stream_name:
                    if row[1] != '':
                        return True
    return False

def log_stream_info(stream_name: str, broadcast_id: str, pid: int = None):
    logger = pd.read_csv("stream_pid_logger.csv", dtype='string')
    if len(logger) == 0:
        logger = pd.DataFrame([(stream_name, "", broadcast_id)], columns=["stream_name","pid","broadcast_id"], dtype="string")
    elif pid is None:
        new_row = pd.DataFrame([(stream_name, "", broadcast_id)], columns=["stream_name","pid","broadcast_id"], dtype="string")
        logger = pd.concat([logger, new_row])
    else:
        logger.loc[logger['stream_name'] == stream_name, 'pid'] = str(pid)
    logger.to_csv("stream_pid_logger.csv", index=False)
    return

def delete_stream_info(broadcast_id: str):
    logger = pd.read_csv("stream_pid_logger.csv", dtype='string')
    # delete the row from logger if it matches the stream_name var
    logger = logger[~(logger['broadcast_id'] == broadcast_id)]
    logger.to_csv("stream_pid_logger.csv", index=False)
    return


def create_broadcast(stream_name: str):
    broadcast_id, stream_key = ga.start_new_broadcast(stream_name)
    log_stream_info(stream_name, broadcast_id)
    return broadcast_id, stream_key

def start_ffmpeg(stream_name: str, broadcast_id: str, stream_key: str, secrets: dict):
    STREAM_USERNAME = secrets['stream_username']
    STREAM_PASSWORD = secrets['stream_password']

    # Starts the FFMPEG process in the background
    process = subprocess.Popen([
        "C:\ProgramData\chocolatey\lib\\ffmpeg\\tools\\ffmpeg\\bin\\ffmpeg.exe",
        "-i",
        f"rtsp://{STREAM_USERNAME}:{STREAM_PASSWORD}@192.168.50.215/{stream_name}",
        "-b:v",
        "25k",
        "-vcodec",
        "copy",
        "-acodec",
        "aac",
        "-f",
        "flv",
        f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    ], creationflags=0x00000008) # Creation flag allows process to start in background
    logger.log(f"Started FFMPEG process with PID = {process.pid}")
    log_stream_info(stream_name, broadcast_id, process.pid)

    sleep(10)
    # Transition broadcast from not live state to live state
    ga.broadcast_go_live(broadcast_id)
    
    return broadcast_id

async def broadcast_monitor():
    while(True):
        logger.log("Checking for running broadcasts")
        if os.path.exists('stream_pid_logger.csv'):
            df = pd.read_csv("stream_pid_logger.csv", dtype='string')
            for index, row in df.iterrows():
                broadcast_id = row['broadcast_id']
                close_idle_broadcast(broadcast_id)
        else:
            logger.log("stream_pid_logger.csv does not exist.")
        await asyncio.sleep(300)  # check every 5 minutes

def close_idle_broadcast(broadcast_id):
    viewer_count, runtime = ga.get_broadcast_info(broadcast_id)
    logger.log(f"Stream has been running for {runtime} minutes")
    logger.log(f"Viewer count: {viewer_count}")
    if viewer_count > 0:
        logger.log(f"There are currently {viewer_count} viewers watching the stream.")
    else:
        logger.log("There are no viewers watching the stream. Terminating broadcast.")
        # kill the process with process id = pid
        with open('stream_pid_logger.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[2] == broadcast_id:
                    pid = int(row[1])
                    logger.log(f"Killing process with PID = {pid}")
                    os.kill(pid, 9)  # force kill the process
        ga.terminate_broadcast(broadcast_id)
        delete_stream_info(broadcast_id)