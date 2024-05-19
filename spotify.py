from time import sleep
import spotipy  
from spotipy.oauth2 import SpotifyOAuth  
import json

sample_cadence_data = []

class SpotifyAPI:
    def __init__(self, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI):
        # self.CLIENT_ID="5c17cfd2c3884a6aa0b8d92d21ccf51e"
        # self.CLIENT_SECRET="ce4bd0c559f149aeb281ecfd8d84da9b"
        # self.REDIRECT_URI="http://localhost:3000/callback"
        self.CLIENT_ID=CLIENT_ID
        self.CLIENT_SECRET=CLIENT_SECRET
        self.REDIRECT_URI=REDIRECT_URI
        self.SCOPE = "user-library-read, user-modify-playback-state, user-read-playback-state, user-top-read, user-read-email, user-read-private, playlist-modify-public, playlist-modify-private"
        self.BPM_UNCERTAINTY = 3
        self.CADENCE_INTERVAL_SEC = 3.43
        self.ERROR_THRESHOLD = 5
        self.BPM_THRESHOLD = 110
        self.LOUDNESS_DROP_THRESHOLD = -4
        self.sp = None
        self.sample_cadence_data = None
        self.song_data = {}
        self.device_id = None
        self.device_is_active = False
        self.playback_progress_sec = 0
        self.is_playing = False
        self.current_id = None
        self.seed_tracks = []
        self.seed_genre = []
        self.seed_artist = []
        self.songs_added_to_queue_ids = []
        # self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET, redirect_uri=self.REDIRECT_URI, scope=self.SCOPE))

    def auth(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET, redirect_uri=self.REDIRECT_URI, scope=self.SCOPE))


    def readDataAndAuthenticate(self, combined_list):
        self.sample_cadence_data = combined_list

        #authenticate
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET, redirect_uri=self.REDIRECT_URI, scope=self.SCOPE))

        #populate seed_genre and seed_artist
        self.seed_artist.append(self.sp.current_user_top_artists(limit=1, offset=0, time_range='medium_term')['items'][0]['id'])
        self.seed_genre.append(self.sp.current_user_top_artists(limit=1, offset=0, time_range='medium_term')['items'][0]['genres'][0])

    def get_cadence_avg(self, start_time, duration):
        start_index = int(start_time/self.CADENCE_INTERVAL_SEC)
        end_index = int (start_time + int(duration/self.CADENCE_INTERVAL_SEC))
        print("start index", start_index, "end_index", end_index)

        total = sum(self.sample_cadence_data[i] for i in range(start_index, end_index))
        count = end_index - start_index

        average = total / count
        return average
    
    def get_top_songs_data(self, num_songs=10):
        # data = {}

        results = self.sp.current_user_top_tracks(limit=num_songs, offset=0, time_range='medium_term')
        for idx, item in enumerate(results['items']):
            id = item['id']
            name = item['name']
            duration = round(item['duration_ms']/1000, 2)
            uri = item['uri']

            self.song_data[id] = {"name" : name, "duration" : duration, "uri" : uri}
            if idx < 3:
                self.seed_tracks.append(str(id))

            print(idx+1, name, duration, id, uri) 

        # print("seed_tracks: " + self.seed_tracks)

        # bpm_arr = []
        # running_bpm_arr = []
        for id in self.song_data:
            result = self.sp.audio_analysis(track_id=id)
            bpm = result['track']['tempo']
            self.song_data[id]['bpm'] = bpm
            print(bpm)
            
            # double it if it is too low
            running_bpm = bpm
            if bpm < self.BPM_THRESHOLD:
                running_bpm *= 2
            
            # running_bpm_arr.append(running_bpm)
            # bpm_arr.append(bpm)
            self.song_data[id]['running_bpm'] = running_bpm
        
        return self.song_data
    
    #todo add_songs()
    def add_recommended_songs(self):
        new_songs = {}

        results = self.sp.recommendations(seed_artists=self.seed_artist, seed_genres=self.seed_genre, seed_tracks=self.seed_tracks)

        for idx, item in enumerate(results['tracks']):
            id = item['id']
            name = item['name']
            duration = round(item['duration_ms']/1000, 2)
            uri = item['uri']

            new_songs[id] = {"name" : name, "duration" : duration, "uri" : uri}
            
            print("ADDED", idx+1, name, duration, id, uri) 

        for id in new_songs:
            result = self.sp.audio_analysis(track_id=id)
            bpm = result['track']['tempo']
            new_songs[id]['bpm'] = bpm
            print(bpm)
            
            # double it if it is too low
            running_bpm = bpm
            if bpm < 110:
                running_bpm *= 2
            
            # running_bpm_arr.append(running_bpm)
            # bpm_arr.append(bpm)
            new_songs[id]['running_bpm'] = running_bpm
        
        self.song_data.update(new_songs)
        
        return self.song_data


    def add_to_queue(self):
        time_elapsed_sec = 0 # total duration of songs played

        for i in range(5): # todo fix
            target_spm = round(self.get_cadence_avg(time_elapsed_sec, 200) * 2, 2)
            print("Target spm:", target_spm)

            closest_entry = min(self.song_data.items(), key=lambda item: abs(item[1]['running_bpm'] - target_spm))
            print(closest_entry)

            error = abs(closest_entry[1]['running_bpm'] - target_spm)

            print("\nError:", error, "\n")

            if error > self.ERROR_THRESHOLD:
                print('below error threshold')

                self.add_recommended_songs()

            else:
                # add a song to queue
                self.sp.add_to_queue(uri=closest_entry[1]['uri']) # todo set default device when no active device is detected
                print(f"Added {closest_entry[1]['name']} to queue")
                self.songs_added_to_queue_ids.append(closest_entry[0])

                del self.song_data[closest_entry[0]]

                time_elapsed_sec += closest_entry[1]['duration']
                print("Current length of queue (sec):", round(time_elapsed_sec, 2))

            sleep(5) # todo fix 

# result = sp.audio_analysis("4pi0Elz7B7cLfw37J3bYm9")
    # given sections array of a song, returns sections where there is a suddenly decrease in loudness
    def get_loudness_drop_sections(self, sections):
        if len(sections) < 1:
            return None
        
        print(type(sections))
        prev = sections[0]['loudness']
        res = []

        for section in sections:
            if section['loudness'] - prev < self.LOUDNESS_DROP_THRESHOLD:
                print("Detected loudness drop")
                res.append(section)
            prev = section['loudness']
        
        return res

    def update_playback_state(self):
        playback_state = self.sp.current_playback()
        self.device_id = playback_state['device']['id']
        self.device_is_active = playback_state['device']['is_active']
        self.playback_progress_sec = round(playback_state['progress_ms']/1000, 2)
        self.is_playing =  playback_state['is_playing']
        self.current_id = playback_state['item']['id']

    # monitors for when to skip songs
    def monitor_playback(self):

        while True:
            self.update_playback_state()

            if self.is_playing:
                result = self.sp.audio_analysis(self.current_id)
                target_sections = self.get_loudness_drop_sections(result['sections'])
                print(target_sections)
                if target_sections:
                    self.update_playback_state()
                    target_time = target_sections[0]['start']
                    print("target skip time", target_time)
                    sleep_time = target_time - self.playback_progress_sec 
                    print("sleeping", sleep_time)

                    sleep(sleep_time)
                    # self.update_playback_state()

                    # if abs(self.playback_progress_sec - target_time) < 0.5:
                    self.sp.next_track()
            
    # creates playlist with items added to queue and all songs played so far
    def create_playlist(self, playlist_name='My awesome running playlist'):
        print("Creating playlist")
        user_id = self.sp.current_user()['id']
        result = self.sp.user_playlist_create(user=user_id, name=playlist_name, public=False)
        playlist_id = result['id']
        if self.songs_added_to_queue_ids:
            self.sp.user_playlist_add_tracks(user=user_id, playlist_id=playlist_id, tracks=self.songs_added_to_queue_ids)

        

    
    # returns currently playing and queue, e.g. {'currently_playing': None, 'queue': []}
    def get_playing_and_queue(self):
        return self.sp.queue()
    
# spotify = SpotifyAPI()
# spotify.readDataAndAuthenticate()
# spotify.get_top_songs_data()
# spotify.add_to_queue()
# spotify.create_playlist()