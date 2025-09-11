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
    stream_username = secrets['stream_username']
    stream_password = secrets['stream_password']
    stream_name = secrets['stream_names'][0]
     #print(f"testing {secrets['stream_names'][0]}")

    access_code = ac.generate_access_code()
    ga.start_yt_broadcast()
    sleep(5)
    subprocess.run(['ffmpeg',
                    '-i',
                    'rtsp://{stream_username}:{stream_password}@192.168.50.215/{stream_name}',
                    '-vcodec',
                    'copy',
                    '-acodec',
                    'aac',
                    '-f',
                    'flv',
                    'rtmp://a.rtmp.youtube.com/live2/4zh4-9gbe-zyg6-qqhx-8vxs'
                    ], capture_output=False)

    return f"Today's access_code = {access_code}"