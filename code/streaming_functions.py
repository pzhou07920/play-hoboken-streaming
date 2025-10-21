import logger
from time import sleep
import google_auth as ga
import subprocess
import csv
import os
import pandas as pd
import asyncio
import requests

def at_broadcast_limit(broadcast_limit: int):
    # check if broadcast_db.csv exists, if not create it and add header
    if os.path.exists('broadcast_db.csv'):
        logger.log("broadcast_db.csv exists!")
    else:
        with open('broadcast_db.csv', 'x', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['stream_name', 'pid', 'broadcast_id'])

    with open('broadcast_db.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        # count the number of rows in the csv file
        row_count = sum(1 for row in reader) - 1  # subtract 1 for header
        logger.log(f"Current number of broadcasts: {row_count}")
        if row_count >= broadcast_limit:
            logger.log(f"At broadcast limit of {broadcast_limit}. Cannot start new broadcast.")
            return True
        else:
            return False

def stream_is_live(stream_name: str):
    # make an API request to nginx/stream_name and retrieve the broadcast_id from the response youtube url
    redirect_url = f"https://stream2.playhoboken.com/{stream_name}"
    response = requests.get(redirect_url, verify=False)
    if response.status_code == 200:
        redirect_url = response.url
        logger.log(f"Redirect URL: {redirect_url}")
        path_segments = redirect_url.split('/')
        broadcast_id = path_segments[-1]  # The last segment is the broadcast ID
        if ga.broadcast_is_live(broadcast_id):
            logger.log(f"Stream {stream_name} is live.")
            return True
        else:
            logger.log(f"Stream {stream_name} is not live.")
            return False
    else:
        logger.log(f"Did not receive a 200 from {redirect_url} | Received status code: {response.status_code}")
    return False

def ffmpeg_running(stream_name: str):
    if os.path.exists('broadcast_db.csv'):
        with open('broadcast_db.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                if row[0] == stream_name:
                    if row[1] != '':
                        return True
    return False

def log_stream_info(stream_name: str, broadcast_id: str, pid: int = None):
    broadcast_df = pd.read_csv("broadcast_db.csv", dtype='string')
    logger.log(f"Logging stream info for {stream_name} | Broadcast ID: {broadcast_id} | PID: {pid}")
    if pid is None:
        new_row = pd.DataFrame([(stream_name, "", broadcast_id)], columns=["stream_name","pid","broadcast_id"], dtype="string")
        broadcast_df = pd.concat([broadcast_df, new_row])
    else:
        broadcast_df.loc[(broadcast_df['stream_name'] == stream_name) & (broadcast_df['broadcast_id'] == broadcast_id), 'pid'] = str(pid)
    broadcast_df.to_csv("broadcast_db.csv", index=False)
    return

def delete_stream_info(broadcast_id: str):
    logger = pd.read_csv("broadcast_db.csv", dtype='string')
    # delete the row from logger if it matches the stream_name var
    logger = logger[~(logger['broadcast_id'] == broadcast_id)]
    logger.to_csv("broadcast_db.csv", index=False)
    return


def create_broadcast(stream_name: str):
    broadcast_id, stream_key = ga.start_new_broadcast(stream_name)
    log_stream_info(stream_name, broadcast_id)
    return broadcast_id, stream_key

def start_ffmpeg(stream_name: str, broadcast_id: str, stream_key: str, secrets: dict):
    STREAM_USERNAME = secrets['stream_username']
    STREAM_PASSWORD = secrets['stream_password']

    camera_name = secrets['camera_stream_mapping'][stream_name]
    logger.log(f"Starting FFMPEG for stream: {stream_name} | Camera Name: {camera_name}")

    # Starts the FFMPEG process in the background
    # Sample FFMPEG command: # ffmpeg.exe -i "rtsp://admin:spot9666@192.168.50.215/Preview_02_main" -b:v 25k -vcodec copy -acodec aac -f flv "rtmp://a.rtmp.youtube.com/live2/jk9h-z547-97uv-q42j-0944"
    process = subprocess.Popen([
        "C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin\\ffmpeg.exe",
        "-i",
        f"rtsp://{STREAM_USERNAME}:{STREAM_PASSWORD}@192.168.50.215/{camera_name}",
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

    # print(process)
    # logger.log(f"error code: {process.returncode}")
    logger.log(f"Started FFMPEG process with PID = {process.pid}")
    log_stream_info(stream_name, broadcast_id, process.pid)
    
    sleep(12) # wait for ffmpeg to start
    # Transition broadcast from not live state to live state
    ga.broadcast_go_live(broadcast_id)
    
    return broadcast_id

async def broadcast_monitor():
    while(True):
        logger.log("Checking for running broadcasts")
        broadcasts = ga.get_active_broadcasts()
        for broadcast in broadcasts:
            broadcast_id = broadcast['id']
            if ga.broadcast_is_live(broadcast_id):
                close_idle_broadcast(broadcast_id)
        await asyncio.sleep(1200)  # check every 20 minutes

def close_idle_broadcast(broadcast_id):
    viewer_count, runtime = ga.get_broadcast_info(broadcast_id)
    logger.log(f"Stream has been running for {runtime} minutes")
    logger.log(f"Viewer count: {viewer_count}")
    if viewer_count == 0:
        if runtime > 10:
            logger.log("There are no viewers watching the stream. Terminating broadcast.")
            # kill the process with process id = pid
            with open('broadcast_db.csv', 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row[2] == broadcast_id:
                        pid = int(row[1])
                        logger.log(f"Killing process with PID = {pid}")
                        os.kill(pid, 9)  # force kill the process
            ga.terminate_broadcast(broadcast_id)
            delete_stream_info(broadcast_id)

def update_nginx_stream_urls(nginx_path: str, stream_name: str, broadcast_id: str):
    stream_urls_path = f"{nginx_path}\\conf\\stream_urls.conf"
    youtube_url = f"https://www.youtube.com/embed/{broadcast_id}"
    with open(stream_urls_path, "r") as f:
        lines = f.readlines()
    with open(stream_urls_path, "w") as f:
        for line in lines:
            parts = line.strip().split()
            if parts[1] == '$' + stream_name:
                f.write(f"set ${stream_name} {youtube_url};\n")
            else:
                f.write(line)

def reload_nginx(nginx_path: str = None):
    subprocess.Popen([f"{nginx_path}\\nginx.exe", "-s", "reload"], cwd=nginx_path)
    logger.log("Reloaded NGINX configuration")