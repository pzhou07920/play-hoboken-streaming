from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.auth.exceptions
import os
import datetime

def google_auth():

    SCOPES=['https://www.googleapis.com/auth/youtube']
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            creds.refresh(Request())
        except google.auth.exceptions.RefreshError as error:
            # if refresh token fails, reset creds to none.
            creds = None
            print(f'Refresh token expired requesting authorization again: {error}')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes=SCOPES)
            # flow.redirect_uri = 'http://localhost/'
            creds = flow.run_local_server(port=8000, prompt='consent')
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    yt_client = build(API_SERVICE_NAME, API_VERSION, credentials = creds)
    return yt_client

def start_yt_broadcast():
    yt_client = google_auth()
    current_time = datetime.datetime.now(datetime.timezone.utc)
    time_1_min = datetime.timedelta(seconds=10)
    sched_time = (current_time + time_1_min).isoformat()
    print(f'Current Time is {current_time}')
    print(f'Scheduled Time is {sched_time}')
    response = yt_client.liveBroadcasts().insert(
        part="snippet,status",
        body={
          "snippet": {
            "title": "Test Broadcast",
            "scheduledStartTime": sched_time
          },
          "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False
          }
        }
    )

    print(response.execute())

# start_yt_broadcast()