from multiprocessing import process
from fastapi import FastAPI, Query
import yaml
import streaming_functions as sf
import google_auth as ga
from time import sleep
import threading

app = FastAPI()

@app.get("/stream")
async def stream(stream_name: str = Query(None)):
    # read in secrets.yml
    with open("secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)

    stream_name = stream_name.lower().capitalize()
    print("capitalized stream_name " + stream_name)

    ga.google_auth()

    if sf.at_broadcast_limit(secrets['broadcast_limit']):
        return f"At broadcast limit of {secrets['broadcast_limit']}. Cannot start new broadcast."

    # check if stream is already running
    if not sf.stream_already_running(stream_name):
        broadcast_id = sf.create_stream(stream_name, secrets)

        print("Starting thread to close idle broadcast after 15 minutes")
        print(broadcast_id)
        thread = threading.Thread(target=sf.close_idle_broadcast, args=(broadcast_id,))
        thread.start()

        return f"Stream has been started! Watch the stream here: https://www.youtube.com/live/{broadcast_id}"
    else:
        broadcast_id = sf.get_running_stream(stream_name)
        return f"Stream {stream_name} is already running. Watch the stream here: https://www.youtube.com/live/{broadcast_id}"

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
            count += 1
            sleep(20)
    print(f"Stream has been started! Watch the stream here: https://www.youtube.com/live/{broadcast_id}")
    return "Multi-stream test completed."