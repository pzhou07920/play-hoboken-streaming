# Generate a basic API using FastAPI that returns "Hello World"
import access_code as ac
from fastapi import FastAPI
import subprocess
import requests
import google_auth as ga
from time import sleep

app = FastAPI()

@app.get("/stream")
async def stream():
    access_code = ac.generate_access_code()
    ga.start_yt_broadcast()
    sleep(5)
    subprocess.run(['ffmpeg',
                    '-i',
                    'rtsp://admin:spot9666@192.168.50.215/Preview_01_main',
                    '-vcodec',
                    'copy',
                    '-acodec',
                    'aac',
                    '-f',
                    'flv',
                    'rtmp://a.rtmp.youtube.com/live2/4zh4-9gbe-zyg6-qqhx-8vxs'
                    ])

    response = requests.post("https://www.googleapis.com/youtube/v3/liveBroadcasts")

    return f"Today's access_code = {access_code}"