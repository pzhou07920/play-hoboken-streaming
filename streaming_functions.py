from time import sleep
import google_auth as ga
import subprocess

def create_stream(stream_name: str, secrets: dict):
    STREAM_USERNAME = secrets['stream_username']
    STREAM_PASSWORD = secrets['stream_password']

    stream_name = stream_name.lower().capitalize()
    print("capitalized stream_name " + stream_name)
    # access_code = ac.generate_access_code()

    broadcast_id, stream_id, stream_key = ga.start_new_broadcast(stream_name)
    sleep(5)

    pid = subprocess.run([
        "Powershell.exe",
        "Start-Process",
        "-FilePath",
        "ffmpeg.exe",
        "-ArgumentList",
        "\"-i",
        f"rtsp://{STREAM_USERNAME}:{STREAM_PASSWORD}@192.168.50.215/{stream_name}",
        "-vcodec",
        "copy",
        "-acodec",
        "aac",
        "-f",
        "flv",
        f"rtmp://a.rtmp.youtube.com/live2/{stream_key}\""
    ], shell=True, capture_output=False)

    print("sleeping...")
    sleep(30)
    ga.broadcast_go_live(broadcast_id)
    print(f"Started FFMPEG process with PID = {pid}")
    return broadcast_id
