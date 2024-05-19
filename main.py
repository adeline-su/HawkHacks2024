from combiner import Combiner
from cadence import StravaAPI, ActivityType
from dotenv import load_dotenv
from spotify import *
import requests
import webbrowser
from spotipy import oauth2


import os

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:3000'
CLIENT_ID_SPOTIFY='5c17cfd2c3884a6aa0b8d92d21ccf51e'
CLIENT_SECRET_SPOTIFY='ce4bd0c559f149aeb281ecfd8d84da9b'
REDIRECT_URI_SPOTIFY='http://localhost:3000/callback'

SCOPE = "user-library-read, user-modify-playback-state, user-read-playback-state, user-top-read, user-read-email, user-read-private, playlist-modify-public, playlist-modify-private"
sp_oauth = oauth2.SpotifyOAuth( CLIENT_ID_SPOTIFY, CLIENT_SECRET_SPOTIFY,REDIRECT_URI_SPOTIFY,scope=SCOPE )
code = 'AQDXcEcgId827WW9f_yh1uig_Ka47eFu4nz2wfA5sgEioxduqBMKv_gCWt8e3jQ9C_Bm-lnUoIMgH7f27IUV8BTf1DfWErazHsHtWPbYEtwp1xgixIC2JfmD_Nmurj1N7KHsWEKNdyFbbuvy4VW2fiMNlb05MpccC80c_afVoGxDDTx5YtxmN0DPeE-zThkwyQ6uVK0z0hvlcKZJ1hjgyKr_M6CyfWwUjZa4hk6UqPKWLqXB0t5QNce0nq3lu0JABBqrxH6VKxAGvViq9j4RqMW2hjziNLtegQu9nI0d10WrtPsAcLVmq9wLaULzLttPobrsGFgy3XClNcmwIA9uJHLD7UIs933aHYbjd4iC2bY-yMxT7KyXhAJA1l_KEumPH0PJhKDp8rcK_XZM3-5V'
token_info = sp_oauth.get_access_token(code)
access_token = token_info['access_token']
print(access_token)

spotify = SpotifyAPI(CLIENT_ID_SPOTIFY, CLIENT_SECRET_SPOTIFY, REDIRECT_URI_SPOTIFY)
sp = spotipy.Spotify(access_token)
results = sp.current_user()
spotify.sp = sp
print(sp)


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
print(1)
spotify = SpotifyAPI(CLIENT_ID_SPOTIFY, CLIENT_SECRET_SPOTIFY, REDIRECT_URI_SPOTIFY)
print(2)

spotify.auth()
print(3)
spotify.readDataAndAuthenticate(combined_list)
spotify.get_top_songs_data()
spotify.add_to_queue()

# song_data = get_top_songs_data()
# add_to_queue(song_data)
