import logger
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.auth.exceptions
import os
import datetime

def google_auth():
    logger.log("Authenticating to Google...")

    SCOPES=['https://www.googleapis.com/auth/youtube']
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    creds = None
    if os.path.exists('config/token.json'):
        try:
            logger.log("Loading credentials from token.json")
            creds = Credentials.from_authorized_user_file('config/token.json', SCOPES)
            creds.refresh(Request())
        except google.auth.exceptions.RefreshError as error:
            # if refresh token fails, reset creds to none.
            creds = None
            logger.log(f'Refresh token expired requesting authorization again: {error}')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.log("Refreshing token...")
            creds.refresh(Request())
        else:
            logger.log("Fetching new token...")
            flow = InstalledAppFlow.from_client_secrets_file('config/client_secret.json', scopes=SCOPES)
            creds = flow.run_local_server(port=8001, prompt='consent')
        # Save the credentials for the next run
        with open('config/token.json', 'w') as token:
            logger.log("Saving credentials to config/token.json")
            token.write(creds.to_json())
    global yt_client
    yt_client = build(API_SERVICE_NAME, API_VERSION, credentials = creds)
    return

def start_yt_broadcast(stream_title):
    logger.log(f'Starting YouTube Broadcast with title: {stream_title}')
    current_time = datetime.datetime.now(datetime.timezone.utc)
    time_10_sec = datetime.timedelta(seconds=10)
    sched_time = (current_time + time_10_sec).isoformat()

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

    broadcast_id = response.get('id')
    return broadcast_id

def start_yt_livestream():
    logger.log('Starting YouTube Live Stream')
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

    #logger.log(response)
    stream_key = response.get('id')
    # logger.log(f'Stream Key is: {stream_key}')
    return stream_key

def bind_broadcast_to_stream(broadcast_id, stream_id):

    logger.log(f'Binding Broadcast {broadcast_id} to Stream {stream_id}')
    response = yt_client.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    ).execute()

    #logger.log(f"Bind response: {response}")

def get_streamkey(stream_id):
    #yt_client = google_auth()
    logger.log(f'Getting Stream Key for Stream ID: {stream_id}')
    response = yt_client.liveStreams().list(
        part="snippet,cdn",
        mine=True
    ).execute()

    #logger.log(response)
    # get the Stream Key for the item with id = stream_id
    for item in response.get('items', []):
        if item['id'] == stream_id:
            stream_key = item['cdn']['ingestionInfo']['streamName']
            # logger.log(f'Stream Key is: {stream_key}')
            return stream_key
        
def start_new_broadcast(stream_title):
    #yt_client = google_auth()
    broadcast_id = start_yt_broadcast(stream_title)
    stream_id = start_yt_livestream()
    bind_broadcast_to_stream(broadcast_id, stream_id)
    stream_key = get_streamkey(stream_id)
    return broadcast_id, stream_key

def broadcast_go_live(broadcast_id):
    logger.log(f"Going live with broadcast: {broadcast_id}")
    response = yt_client.liveBroadcasts().transition(
        part="id,snippet,contentDetails,status",
        broadcastStatus='live',
        id=broadcast_id,
    ).execute()
   #"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?part=id,snippet,contentDetails,status&broadcastStatus=live&id=$BROADCAST_ID"

def broadcast_is_live(broadcast_id):
    logger.log(f'Checking if Broadcast ID: {broadcast_id} is live')
    response = yt_client.liveBroadcasts().list(
        part="snippet,contentDetails,status",
        id=broadcast_id
    ).execute()

    #logger.log(response)
    for item in response.get('items', []):
        if item['id'] == broadcast_id:
            status = item['status']['lifeCycleStatus']
            logger.log(f'Broadcast Status is: {status}')
            if status == 'active':
                return True
            else:
                return False
    return False

def get_stream_status(stream_id):
    #yt_client = google_auth()
    logger.log(f'Getting Stream Status for Stream ID: {stream_id}')
    response = yt_client.liveStreams().list(
        part="snippet,cdn,status",
        mine=True
    ).execute()

    #logger.log(response)
    # get the Stream Key for the item with id = stream_id
    for item in response.get('items', []):
        if item['id'] == stream_id:
            logger.log(item)

def terminate_broadcast(broadcast_id):
    #google_auth()
    logger.log(f'Terminating Broadcast ID: {broadcast_id}')
    response = yt_client.liveBroadcasts().transition(
        part="id,snippet,contentDetails,status",
        broadcastStatus='complete',
        id=broadcast_id,
    ).execute()
    
def get_broadcast_info(broadcast_id):
    #google_auth()
    logger.log(f'Getting Viewer Count for Broadcast ID: {broadcast_id}')
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
            logger.log(f'Start Time is: {start_time_str}')
            start_time = datetime.datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            current_time = datetime.datetime.now(datetime.timezone.utc)
            runtime = (current_time - start_time).total_seconds() / 60  # runtime in minutes
            runtime = int(runtime)
            logger.log(f'Runtime is: {runtime} minutes')
            viewer_count = item['statistics']['concurrentViewers']
            logger.log(f'Viewer Count is: {viewer_count}')
    return int(viewer_count), runtime

def get_all_broadcasts():
    #google_auth()
    logger.log('Getting All Broadcasts')
    response = yt_client.liveBroadcasts().list(
        part="snippet,contentDetails,status",
        broadcastStatus='active',
        maxResults=25
    ).execute()

    broadcasts = []
    for item in response.get('items', []):
        broadcast_id = item['id']
        title = item['snippet']['title']
        status = item['status']['lifeCycleStatus']
        broadcasts.append({'id': broadcast_id, 'title': title, 'status': status})
        logger.log(f'Broadcast ID: {broadcast_id} | Title: {title} | Status: {status}')
    return broadcasts