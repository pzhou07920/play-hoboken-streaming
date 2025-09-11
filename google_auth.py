import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Required, call the from_client_secrets_file method to retrieve the client ID from a
# client_secret.json file. The client ID (from that file) and access scopes are required. (You can
# also use the from_client_config method, which passes the client configuration as it originally
# appeared in a client secrets file but doesn't access the file itself.)
flow = InstalledAppFlow.from_client_secrets_file('client_secret.json',
    scopes=['https://www.googleapis.com/auth/youtube'])

# Required, indicate where the API server will redirect the user after the user completes
# the authorization flow. The redirect URI is required. The value must exactly
# match one of the authorized redirect URIs for the OAuth 2.0 client, which you
# configured in the API Console. If this value doesn't match an authorized URI,
# you will get a 'redirect_uri_mismatch' error.
flow.redirect_uri = 'http://localhost/'

creds = flow.run_local_server(port=8000)
with open('token.json', 'w') as token:
            token.write(creds.to_json())


# import googleapiclient.discovery

# # API information
# api_service_name = "youtube"
# api_version = "v3"
# # API key
# DEVELOPER_KEY = ""
# # API client
# youtube = googleapiclient.discovery.build(
#     api_service_name, api_version, developerKey = DEVELOPER_KEY)

# request=youtube.liveBroadcasts().insert(
#     part="snippet,status",
#     body={
#       "snippet": {
#         "title": "Test Broadcast",
#         "scheduledStartTime": "2025-09-10T18:00:00Z"
#       },
#       "status": {
#         "privacyStatus": "private"
#       }
#     }
# )

# response = request.execute()