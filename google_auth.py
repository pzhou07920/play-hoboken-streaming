from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.auth.exceptions
import os
import datetime

def google_auth():
    print("Authenticating to Google...")

    SCOPES=['https://www.googleapis.com/auth/youtube']
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    creds = None
    if os.path.exists('token.json'):
        try:
            print("Loading credentials from token.json")
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            creds.refresh(Request())
        except google.auth.exceptions.RefreshError as error:
            # if refresh token fails, reset creds to none.
            creds = None
            print(f'Refresh token expired requesting authorization again: {error}')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(Request())
        else:
            print("Fetching new token...")
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes=SCOPES)
            creds = flow.run_local_server(port=8001, prompt='consent')
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            print("Saving credentials to token.json")
            token.write(creds.to_json())
    global yt_client
    yt_client = build(API_SERVICE_NAME, API_VERSION, credentials = creds)
    return

def start_yt_broadcast(stream_title):
    #yt_client = google_auth()

    print(f'Starting YouTube Broadcast with title: {stream_title}')
    current_time = datetime.datetime.now(datetime.timezone.utc)
    time_10_sec = datetime.timedelta(seconds=10)
    sched_time = (current_time + time_10_sec).isoformat()
    # print(f'Current Time is {current_time}')
    print(f'Scheduled Time is {sched_time}')
    response = yt_client.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
          "snippet": {
            "title": f"{stream_title}",
            "scheduledStartTime": sched_time
          },
          "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
          },
          "contentDetails": {
            "enableAutoStart": False,
            "monitorStream" : {
              "enableMonitorStream": False
            }
          }
        }
    ).execute()

    #print(response)
    broadcast_id = response.get('id')
    print(f'Broadcast ID is: {broadcast_id}')
    return broadcast_id

def start_yt_livestream():
    #yt_client = google_auth()

    print('Starting YouTube Live Stream')
    response = yt_client.liveStreams().insert(
        part="snippet,cdn,contentDetails",
        body={
          "snippet": {
            "title": "Test Stream",
            "description": "This is a test stream"
          },
          "cdn": {
            "frameRate": "30fps",
            "ingestionType": "rtmp",
            "resolution": "720p"
          },
          "contentDetails": {
            "isReusable": True
          }
        }
    ).execute()

    #print(response)
    stream_key = response.get('id')
    print(f'Stream Key is: {stream_key}')
    return stream_key

def bind_broadcast_to_stream(broadcast_id, stream_id):
    #yt_client = google_auth()
    #broadcast_id = start_yt_broadcast(yt_client, "Test Bind")
    #stream_id = start_yt_livestream(yt_client)
    #broadcast_id = "b7k7x1l6o4c"

    print(f'Binding Broadcast {broadcast_id} to Stream {stream_id}')
    response = yt_client.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    ).execute()

    #print(f"Bind response: {response}")

#bind_broadcast_to_stream()
# start_yt_livestream( )
#start_yt_broadcast("Test Stream from API") 

def get_streamkey(stream_id):
    #yt_client = google_auth()
    print(f'Getting Stream Key for Stream ID: {stream_id}')
    response = yt_client.liveStreams().list(
        part="snippet,cdn",
        mine=True
    ).execute()

    #print(response)
    # get the Stream Key for the item with id = stream_id
    for item in response.get('items', []):
        if item['id'] == stream_id:
            stream_key = item['cdn']['ingestionInfo']['streamName']
            print(f'Stream Key is: {stream_key}')
            return stream_key
        
def start_new_broadcast(stream_title):
    #yt_client = google_auth()
    broadcast_id = start_yt_broadcast(stream_title)
    stream_id = start_yt_livestream()
    bind_broadcast_to_stream(broadcast_id, stream_id)
    stream_key = get_streamkey(stream_id)
    return broadcast_id, stream_key

def broadcast_go_live(broadcast_id):
    print(f"Going live with broadcast: {broadcast_id}")
    response = yt_client.liveBroadcasts().transition(
        part="id,snippet,contentDetails,status",
        broadcastStatus='live',
        id=broadcast_id,
    ).execute()
   #"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?part=id,snippet,contentDetails,status&broadcastStatus=live&id=$BROADCAST_ID"

def get_stream_status(stream_id):
    #yt_client = google_auth()
    print(f'Getting Stream Status for Stream ID: {stream_id}')
    response = yt_client.liveStreams().list(
        part="snippet,cdn,status",
        mine=True
    ).execute()

    #print(response)
    # get the Stream Key for the item with id = stream_id
    for item in response.get('items', []):
        if item['id'] == stream_id:
            print(item)

def terminate_broadcast(broadcast_id):
    #yt_client = google_auth()
    print(f'Terminating Broadcast ID: {broadcast_id}')
    response = yt_client.liveBroadcasts().transition(
        part="id,snippet,contentDetails,status",
        broadcastStatus='complete',
        id=broadcast_id,
    ).execute()
    
def get_broadcast_info(broadcast_id):
    yt_client = google_auth()
    print(f'Getting Viewer Count for Broadcast ID: {broadcast_id}')
    response = yt_client.liveBroadcasts().list(
        part="snippet,contentDetails,statistics",
        id=broadcast_id
    ).execute()

    # get stream runtime
    runtime = 0
    start_time_str = ""
    for item in response.get('items', []):
        if item['id'] == broadcast_id:
            start_time_str = item['snippet']['actualStartTime']
            print(f'Start Time is: {start_time_str}')
            start_time = datetime.datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            current_time = datetime.datetime.now(datetime.timezone.utc)
            runtime = (current_time - start_time).total_seconds() / 60  # runtime in minutes
            runtime = int(runtime)
            print(f'Runtime is: {runtime} minutes')
            break
        if item['id'] == broadcast_id:
            viewer_count = item['statistics']['concurrentViewers']
            print(f'Viewer Count is: {viewer_count}')
    return viewer_count, runtime

