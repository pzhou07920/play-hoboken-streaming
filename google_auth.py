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
    yt_client = build(API_SERVICE_NAME, API_VERSION, credentials = creds)
    return yt_client

def start_yt_broadcast(yt_client, stream_title):
    #yt_client = google_auth()

    print(f'Starting YouTube Broadcast with title: {stream_title}')
    current_time = datetime.datetime.now(datetime.timezone.utc)
    time_10_sec = datetime.timedelta(seconds=10)
    sched_time = (current_time + time_10_sec).isoformat()
    print(f'Current Time is {current_time}')
    print(f'Scheduled Time is {sched_time}')
    response = yt_client.liveBroadcasts().insert(
        part="snippet,status",
        body={
          "snippet": {
            "title": f"{stream_title}",
            "scheduledStartTime": sched_time
          },
          "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
          }
        }
    ).execute()

    broadcast_id = response.get('id')
    print(f'Broadcast ID is: {broadcast_id}')
    return broadcast_id

def start_yt_livestream(yt_client):
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

    stream_key = response.get('cdn').get('ingestionInfo').get('streamName')
    print(f'Stream Key is: {stream_key}')
    return stream_key

def bind_stream():
    yt_client = google_auth()
    broadcast_id = start_yt_broadcast(yt_client, "Test Bind")
    stream_id = start_yt_livestream(yt_client)
    #broadcast_id = "b7k7x1l6o4c"
    print(f'Binding Broadcast {broadcast_id} to Stream {stream_id}')
    response = yt_client.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    ).execute()

    print(f"Bind response: {response}")

bind_stream()
#start_yt_livestream()
#start_yt_broadcast("Test Stream from API")