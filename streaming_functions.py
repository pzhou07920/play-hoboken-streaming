from time import sleep
import google_auth as ga
import subprocess
import csv
import os

def at_broadcast_limit(broadcast_limit: int):
    with open('stream_pid_tracker.csv', 'a', newline='') as csvfile:
        #csvfile.seek(0)
        reader = csv.reader(csvfile)
        # count the number of rows in the csv file
        row_count = sum(1 for row in reader) - 1  # subtract 1 for header
        print(f"Current number of broadcasts: {row_count}")
        if row_count >= broadcast_limit:
            print(f"At broadcast limit of {broadcast_limit}. Cannot start new broadcast.")
            return True
        else:
            return False

def stream_already_running(stream_name: str, pid: int, broadcast_id: str = None):
    # check if stream_pid_tracker.csv exists, if not create it and add header
    if os.path.exists('stream_pid_tracker.csv'):
        print("stream_pid_tracker.csv exists!")
    else:
        with open('stream_pid_tracker.csv', 'x', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['stream_name', 'pid'])

    with open('stream_pid_tracker.csv', 'a', newline='') as csvfile:
        # Check if the stream_name already exists in the csv file
        #csvfile.seek(0)
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == stream_name:
                print(f"Stream {row[0]} with PID {row[1]} and Broadcast ID {row[2]} already exists.")
                return True
    return False

def get_running_stream(stream_name: str):
    if os.path.exists('stream_pid_tracker.csv'):
        with open('stream_pid_tracker.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                if row[0] == stream_name:
                    pid = row[2]
                    broadcast_id = row[3]
                    return stream_name, pid, broadcast_id
    return None

def log_stream_info(stream_name: str, pid: int, broadcast_id: str):
    with open('stream_pid_tracker.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([stream_name, pid, broadcast_id])

def create_stream(stream_name: str, secrets: dict):
    STREAM_USERNAME = secrets['stream_username']
    STREAM_PASSWORD = secrets['stream_password']
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

    log_stream_info(stream_name, process.pid, broadcast_id)

    print("sleeping...")
    sleep(10)
    ga.broadcast_go_live(broadcast_id, stream_id, broadcast_id)
    
    return broadcast_id

def close_idle_broadcast(broadcast_id):
    viewer_count = 1
    while(viewer_count > 0):
        sleep(900)  # check every 15 minutes
        viewer_count, runtime = ga.get_broadcast_info(broadcast_id)
        print(f"Stream has been running for {runtime} minutes")
        print(f"Viewer count: {viewer_count}")
        if viewer_count > 0:
            print(f"There are currently {viewer_count} viewers watching the stream.")
        else:
            print("There are no viewers watching the stream. Terminating broadcast.")
            # kill the process with process id = pid
            with open('stream_pid_tracker.csv', 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row[2] == broadcast_id:
                        pid = int(row[1])
                        print(f"Killing process with PID = {pid}")
                        os.kill(pid, 9)  # force kill the process
