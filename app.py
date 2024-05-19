from flask import Flask, request, jsonify, redirect, session
from combiner import Combiner
from cadence import *
from dotenv import load_dotenv
from spotify import *
import urllib.parse
import os

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
CLIENT_ID_SPOTIFY = os.getenv('CLIENT_ID_SPOTIFY')
CLIENT_SECRET_SPOTIFY=os.getenv('CLIENT_SECRET_SPOTIFY')
REDIRECT_URI_SPOTIFY=os.getenv('REDIRECT_URI_SPOTIFY')

strava = StravaAPI(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
spotify = SpotifyAPI(CLIENT_ID_SPOTIFY, CLIENT_SECRET_SPOTIFY, REDIRECT_URI_SPOTIFY)
# spotify.auth()
# print(spotify.CLIENT_ID_SPOTIFY, CLIENT_SECRET_SPOTIFY, REDIRECT_URI_SPOTIFY)
# strava.autheticateAndGetAllActivities()
# cadence_data = strava.getCadenceData()

app = Flask(__name__)

REDIRECT_URI_temp = 'https://hawkhacks2024.onrender.com/callback'

# strava authentication
@app.route('/login')
def login():
    auth_url = (
        f'https://www.strava.com/oauth/authorize'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI_temp}'
        f'&response_type=code'
        f'&scope=activity:read_all'
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    print('adeline1')
    code = request.args.get('code')
    print('adeline2')

    #strava auth
    strava.autheticateAndGetAllActivities(code)
    print('adeline3')
    data = strava.getCadenceData(ActivityType.RUN)

    print('adeline4')
    #combiner
    cb = Combiner(arrs=data)
    combined_list = cb.combine()
    print('adeline5')

    # spotify
    spotify.readDataAndAuthenticate(combined_list)

    return jsonify(code)

# spotify authentication
@app.route('/loginspotify')
def loginspotify():
    SCOPE = "user-library-read, user-modify-playback-state, user-read-playback-state, user-top-read, user-read-email, user-read-private, playlist-modify-public, playlist-modify-private"
    auth_url = f'https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID_SPOTIFY}&scope={urllib.parse.quote(SCOPE)}&redirect_uri={REDIRECT_URI_SPOTIFY}'
    return redirect(auth_url)

@app.route('/callbackspotify')
def callbackspotify():
    code = request.args.get('code')
    if not code:
        return 'Error: Authorization code not received'

    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI_SPOTIFY,
        'client_id': CLIENT_ID_SPOTIFY,
        'client_secret': CLIENT_SECRET_SPOTIFY
    }
    response = requests.post('https://accounts.spotify.com/api/token', data=token_data)
    if response.status_code == 200:
        access_token = response.json()['access_token']
        session['access_token'] = access_token
        return 'Authentication successful! You can now access the app.'
    else:
        return 'Error: Failed to retrieve access token'



@app.route('/api/demo', methods=['GET'])
def demo():
    return "Welcome The Flow API"

@app.route('/recent', methods=['GET'])
def getRecent():
    # Call something like stava.getRecent() and return a json
    json = jsonify(strava.getRecentActivities())
    return json
    # return jsonify("Troll")

# @app.route('/start', methods=['GET'])
# def start():
#     spotify.get_top_songs_data()
#     spotify.add_to_queue()

#     return jsonify('started')

@app.route('/playlist', methods=['GET'])
def getPlaylist():
    activity = request.args.get('activity')
    # call like get playlist or somthing bs
    json = jsonify(spotify.get_playing_and_queue())
    return json

@app.route('/api/greeting', methods=['POST'])
def getData():
    data = request.get_json()
    name = data.get('name')
    return f"Hello, {name}!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True) 
    