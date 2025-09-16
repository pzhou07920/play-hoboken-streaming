from time import sleep
import google_auth as ga
import subprocess
import csv
import os

def track_stream_pid(stream_name: str, pid: int):
    # check if stream_pid_tracker.csv exists, if not create it and add header
    if os.path.exists('stream_pid_tracker.csv'):
        print("stream_pid_tracker.csv exists!")
    else:
        with open('stream_pid_tracker.csv', 'x', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['stream_name', 'pid'])

    with open('stream_pid_tracker.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # only add the stream_name and pid if the stream_name does not already exist in the file
        csvfile.seek(0)
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == stream_name:
                print(f"Stream {row[0]} with PID {row[1]} already exists.")
                return
        print(f"Adding stream {stream_name} with PID {pid} to tracker.")
        writer.writerow([stream_name, pid])
        
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

    track_stream_pid(stream_name, process.pid)

    print("sleeping...")
    sleep(10)
    ga.broadcast_go_live(broadcast_id, stream_id)
    
    return broadcast_id
