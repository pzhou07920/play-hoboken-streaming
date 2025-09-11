# Generate a basic API using FastAPI that returns "Hello World"
import access_code as ac
from fastapi import FastAPI
import subprocess
import requests
import google_auth as ga
from time import sleep
import yaml

app = FastAPI()

@app.get("/stream")
async def stream():
    # read in secrets.yml
    with open("secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)
    STREAM_USERNAME = secrets['stream_username']
    STREAM_PASSWORD = secrets['stream_password']
    STREAM_NAME = secrets['stream_names'][0]

    access_code = ac.generate_access_code()
    ga.start_yt_broadcast()
    sleep(5)
    subprocess.run(['ffmpeg',
                    '-i',
                    'rtsp://{STREAM_USERNAME}:{STREAM_PASSWORD}@192.168.50.215/{STREAM_NAME}',
                    '-vcodec',
                    'copy',
                    '-acodec',
                    'aac',
                    '-f',
                    'flv',
                    'rtmp://a.rtmp.youtube.com/live2/4zh4-9gbe-zyg6-qqhx-8vxs'
                    ], capture_output=False)

    return f"Stream has been started! Watch the stream here: https://www.youtube.com/watch?v="