from combiner import Combiner
from cadence import StravaAPI, ActivityType
from dotenv import load_dotenv
from spotify import *
import requests
import webbrowser
import os

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:3000'
CLIENT_ID_SPOTIFY='5c17cfd2c3884a6aa0b8d92d21ccf51e'
CLIENT_SECRET_SPOTIFY='ce4bd0c559f149aeb281ecfd8d84da9b'
REDIRECT_URI_SPOTIFY='http://localhost:3000/callback'

activity_type = ActivityType.RUN # will be dynamic value later

# strava
strava = StravaAPI(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


# # Step 2: Obtain the authorization code
params = {
    'client_id': CLIENT_ID,
    'redirect_uri': REDIRECT_URI,
    'response_type': 'code',
    'scope': 'activity:read_all'
}
auth_request = requests.Request('GET', 'https://www.strava.com/oauth/authorize', params=params).prepare()
auth_url = auth_request.url
print(f'Opening the following URL in your browser: {auth_url}')
webbrowser.open(auth_url)

# Step 3: User authorizes and we get the authorization code from the redirect URL
print('Please authorize the app and paste the full redirect URL here:')
redirect_response = input('> ')
auth_code = redirect_response.split('code=')[1].split('&')[0]


if not strava.autheticateAndGetAllActivities(auth_code):
    print("Error: probably out of access tokens for Strava's API")
    exit()

data = strava.getCadenceData(activity_type)
recent = strava.getRecentActivities()
print(recent)

# combiner
cb = Combiner(arrs=data)

combined_list = cb.combine()
print(combined_list)
print(len(cb.combine()))

# spotify
spotify = SpotifyAPI(CLIENT_ID_SPOTIFY, CLIENT_SECRET_SPOTIFY, REDIRECT_URI_SPOTIFY)
spotify.readDataAndAuthenticate(combined_list)
spotify.get_top_songs_data()
spotify.add_to_queue()

# song_data = get_top_songs_data()
# add_to_queue(song_data)
