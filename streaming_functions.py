from time import sleep
import google_auth as ga
import subprocess

def create_stream(stream_name: str, secrets: dict):
    STREAM_USERNAME = secrets['stream_username']
    STREAM_PASSWORD = secrets['stream_password']

    # access_code = ac.generate_access_code()

    stream_id = ga.start_yt_broadcast(stream_title=stream_name)
    sleep(5)
    # subprocess.run([
    #     "Powershell.exe",
    #     "Start-Process",
    #     "-FilePath",
    #     "ffmpeg.exe",
    #     "-ArgumentList",
    #     "\"-i",
    #     f"rtsp://{STREAM_USERNAME}:{STREAM_PASSWORD}@192.168.50.215/{STREAM_NAME}",
    #     "-vcodec",
    #     "copy",
    #     "-acodec",
    #     "aac",
    #     "-f",
    #     "flv",
    #     "rtmp://a.rtmp.youtube.com/live2/4zh4-9gbe-zyg6-qqhx-8vxs\""
    # ], shell=True, capture_output=False)

    return stream_id
