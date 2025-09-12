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

    process = subprocess.Popen([
        "Powershell.exe",
        "Start-Process",
        "-FilePath",
        "ffmpeg.exe",
        "-ArgumentList",
        "\"-i",
        f"rtsp://{STREAM_USERNAME}:{STREAM_PASSWORD}@192.168.50.215/{stream_name}",
        "-b:v",
        "25k",
        "-vcodec",
        "copy",
        "-acodec",
        "aac",
        "-f",
        "flv",
        f"rtmp://a.rtmp.youtube.com/live2/{stream_key}\""
    ], shell=True)
    print(f"Started FFMPEG process with PID = {process.pid}")

    print("sleeping...")
    sleep(10)
    ga.broadcast_go_live(broadcast_id, stream_id)
    
    return broadcast_id
