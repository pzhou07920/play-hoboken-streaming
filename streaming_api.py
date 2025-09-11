from fastapi import FastAPI, Query
import yaml
import streaming_functions as sf

app = FastAPI()

@app.get("/stream")
async def stream(stream_name: str = Query(None)):
    # read in secrets.yml
    with open("secrets.yml", "r") as f:
        secrets = yaml.safe_load(f)

    stream_id = sf.send_stream(stream_name, secrets)
    return f"Stream has been started! Watch the stream here: https://www.youtube.com/live/{stream_id}"