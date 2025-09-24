import datetime

def log(msg: str):
    time = datetime.datetime.now().strftime("%H:%M:%S")
    log = f"[{time}] {msg}"
    print(log)
    with open("logs.txt", "a") as f:
        f.write(log + "\n")