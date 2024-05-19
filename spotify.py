from time import sleep
import spotipy  
from spotipy.oauth2 import SpotifyOAuth  
import json

# CLIENT_ID="5c17cfd2c3884a6aa0b8d92d21ccf51e"
# CLIENT_SECRET="ce4bd0c559f149aeb281ecfd8d84da9b"
# REDIRECT_URI="http://localhost:3000"
# SCOPE = "user-library-read, user-modify-playback-state, user-read-playback-state, user-top-read"
# BPM_UNCERTAINTY = 3
# CADENCE_INTERVAL_SEC = 3.43

sample_cadence_data = []

class SpotifyAPI:
    def __init__(self):
        self.CLIENT_ID="5c17cfd2c3884a6aa0b8d92d21ccf51e"
        self.CLIENT_SECRET="ce4bd0c559f149aeb281ecfd8d84da9b"
        self.REDIRECT_URI="http://localhost:3000"
        self.SCOPE = "user-library-read, user-modify-playback-state, user-read-playback-state, user-top-read"
        self.BPM_UNCERTAINTY = 3
        self.CADENCE_INTERVAL_SEC = 3.43
        self.ERROR_THRESHOLD = 5
        self.sp = None
        self.sample_cadence_data = None
        self.song_data = {}
        self.seed_tracks = []
        self.seed_genre = []
        self.seed_artist = []

    def readDataAndAuthenticate(self):
        # Read JSON file and assign to variable
        with open('combined.txt', 'r') as file:
            self.sample_cadence_data = json.load(file)

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
            if bpm < 110:
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

        while(True): # todo fix
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

                del self.song_data[closest_entry[0]]

                time_elapsed_sec += closest_entry[1]['duration']
                print("Current length of queue (sec):", round(time_elapsed_sec, 2))

            sleep(10) # todo fix

# # Read JSON file and assign to variable
# with open('combined.txt', 'r') as file:
#     sample_cadence_data = json.load(file)

# # authenticate
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE))


# def get_cadence_avg(start_time, duration):
#     start_index = int(start_time/CADENCE_INTERVAL_SEC)
#     end_index = int (start_time + int(duration/CADENCE_INTERVAL_SEC))
#     print("start index", start_index, "end_index", end_index)

#     total = sum(sample_cadence_data[i] for i in range(start_index, end_index))
#     count = end_index - start_index

#     average = total / count
#     return average

# def get_top_songs_data(num_songs=10):
#     data = {}

#     results = sp.current_user_top_tracks(limit=num_songs, offset=0, time_range='medium_term')
#     for idx, item in enumerate(results['items']):
#         id = item['id']
#         name = item['name']
#         duration = round(item['duration_ms']/1000, 2)
#         uri = item['uri']

#         data[id] = {"name" : name, "duration" : duration, "uri" : uri}
    
#         print(idx+1, name, duration, id, uri) 

#     # bpm_arr = []
#     # running_bpm_arr = []
#     for id in data:
#         result = sp.audio_analysis(track_id=id)
#         bpm = result['track']['tempo']
#         data[id]['bpm'] = bpm
#         print(bpm)
        
#         # double it if it is too low
#         running_bpm = bpm
#         if bpm < 110:
#             running_bpm *= 2
        
#         # running_bpm_arr.append(running_bpm)
#         # bpm_arr.append(bpm)
#         data[id]['running_bpm'] = running_bpm
    
#     return data

# # avg_cadence = round(sum(sample_cadence_data)/len(sample_cadence_data)*2, 2)
# # print(avg_cadence)


# def add_to_queue(song_data):
#     time_elapsed_sec = 0 # total duration of songs played

#     while(True): # todo fix
#         target_spm = round(get_cadence_avg(time_elapsed_sec, 200) * 2, 2)
#         print("Target spm:", target_spm)

#         closest_entry = min(song_data.items(), key=lambda item: abs(item[1]['running_bpm'] - target_spm))
#         print(closest_entry)

#         error = abs(closest_entry[1]['running_bpm'] - target_spm)

#         print("\nError:", error, "\n")

#         if error > 5:
#             print('below error threshold')

#             #todo add songs to song bucket


#         else:
#             # add a song to queue
#             sp.add_to_queue(uri=closest_entry[1]['uri']) # todo set default device when no active device is detected
#             print(f"Added {closest_entry[1]['name']} to queue")

#             del song_data[closest_entry[0]]

#             time_elapsed_sec += closest_entry[1]['duration']
#             print("Current length of queue (sec):", round(time_elapsed_sec, 2))

#         sleep(10) # todo fix
