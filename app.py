from flask import Flask, request, jsonify, redirect
from combiner import Combiner
from cadence import *
from dotenv import load_dotenv
from spotify import *
import os

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

strava = StravaAPI(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
spotify = SpotifyAPI()
spotify.readDataAndAuthenticate()
# strava.autheticateAndGetAllActivities()
# cadence_data = strava.getCadenceData()

app = Flask(__name__)

REDIRECT_URI_temp = 'https://hawkhacks2024.onrender.com/callback'

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
    code = request.args.get('code')

    #strava auth
    strava.autheticateAndGetAllActivities(code)
    data = strava.getCadenceData(ActivityType.RUN)

    #combiner
    cb = Combiner(arrs=data)
    combined_list = cb.combine()

    # spotify
    spotify = SpotifyAPI()
    spotify.readDataAndAuthenticate(combined_list)

    return jsonify(code)


@app.route('/api/demo', methods=['GET'])
def demo():
    return "Welcome The Flow API"

@app.route('/recent', methods=['GET'])
def getRecent():
    # Call something like stava.getRecent() and return a json
    json = jsonify(strava.getRecentActivities())
    return json
    # return jsonify("Troll")

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
    