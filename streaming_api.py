from fastapi import FastAPI, Query
import yaml
import streaming_functions as sf
import google_auth as ga
from time import sleep

app = FastAPI()

@app.get("/stream")
async def stream(stream_name: str = Query(None)):
    # read in secrets.yml
    with open("secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)

    ga.google_auth()
    broadcast_id = sf.create_stream(stream_name, secrets)
    return f"Stream has been started! Watch the stream here: https://www.youtube.com/live/{broadcast_id}"

@app.get("/test_multi_streams")
async def test_multi_streams(stream_count: int = Query(None)):
    # read in secrets.yml
    with open("secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)

    ga.google_auth()
    print(f"Testing {stream_count} streams")
    count = 0
    for stream_name in secrets['stream_names']:
        if count < stream_count:
            print(f"Starting stream: {stream_name}")
            broadcast_id = sf.create_stream(stream_name, secrets)
            sleep(20)
    print(f"Stream has been started! Watch the stream here: https://www.youtube.com/live/{broadcast_id}")
    return "Multi-stream test completed."