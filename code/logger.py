import datetime

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log = f"[{timestamp}] {msg}"
    print(log)
    with open("logs.txt", "a") as f:
        f.write(log + "\n")