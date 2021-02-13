import json
import random
import warnings
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
# from sklearn.model_selection import train_test_split 
# from sklearn.linear_model import LogisticRegression
# from sklearn import metrics
import spotipy
import spotipy.util as util




        


# credentials PATH
CredPath = 'C:\\Users\\ruoyu\\Documents\\DS_Tableau_Projects\\config\\cred_spotify.json'
my_saved_list_req = "https://api.spotify.com/v1/me/tracks?"
song_audio_attributes = 'https://api.spotify.com/v1/audio-features/'#{id}
artist_details = 'https://api.spotify.com/v1/artists/' #{id}

file = open(CredPath)
MyCredential = json.load(file) 
file.close() 

USERNAME = 'bossangelo'
SCOPE = 'user-library-read'
token = util.prompt_for_user_token(USERNAME,
                           SCOPE,
                           client_id=MyCredential['clientID'],
                           client_secret=MyCredential['clientSecret'],
                          # 注意需要在自己的web app中添加redirect url
                           redirect_uri='http://localhost:8080')
# token 你的token，在运行上面的代码后，会显示在http://localhost/里面
HEADER = {"Authorization": "Bearer {}".format(token)}


# attribute list
album_list = []
song_name = []
song_id = []
song_popularity = []
song_duration = [] 
song_artist = []
song_album = []
audio_list = []
#
artist_detail_list = []
artist_genres = []
artist_follower = []

# FUNCS
def get_saved_album(offset = 0):
    try:
        responses = requests.get(my_saved_list_req+f"offset={offset}&limit=50&next=1,", headers=HEADER)   
        myjson_data = json.loads(responses.text)
        spotify_response = pd.DataFrame.from_dict(myjson_data)
        album = spotify_response['items'].to_list()
        album_list.append(album)
    except ValueError as v_err:
        print(f'error occurred: {v_err}') 

## need song ID
def get_song_json(song_id):
    responses = requests.get(song_audio_attributes+f"{song_id}", headers=HEADER)   
    myjson_data = json.loads(responses.text)
    audio_list.append(myjson_data)
    
## need artist ID
def get_artist_json(artist_id):
    responses = requests.get(artist_details+f"{artist_id}", headers=HEADER)   
    myjson_data = json.loads(responses.text)
    artist_detail_list.append(myjson_data)
        
def get_song_info(song_list):
    for song in song_list:
        song_name.append(song['track']['name'])
        song_popularity.append(song['track']['popularity'])
        song_duration.append(song['track']['duration_ms'])
        song_id.append(song['track']['id'])
        # artist info as dict
        artist_info = {}
        artist_info["artist_name"] = song['track']['artists'][0]['name']
        artist_info["artist_type"] = song['track']['artists'][0]['type']
        artist_info["artist_id"] = song['track']['artists'][0]['id']
        song_artist.append(artist_info)
        # album info as dict
        album_info = {}
        album_info["album_name"] = song['track']['album']['name']
        album_info["album_type"] =  song['track']['album']['type']
        album_info["album_id"] = song['track']['album']['id']
        album_info["album_release_date"] = song['track']['album']['release_date']
        album_info["album_cover_url"] = song['track']['album']['images'][0]['url']
        song_album.append(album_info)


def get_artist_info(artist_list):
    for artist in tqdm(artist_list):
        artist_follower.append(artist['followers']['total'])
        artist_genres.append(artist['genres'][0] if artist['genres'] else 'NA') # in case index error
        
def fetch_all(offset_end):
    try:
        print(f"Getting All Pagination...")
        for page in tqdm(range(offset_end)):
            #print(f"Getting Pagination No.{page}")
            get_saved_album(page)
        print('Finished Getting all albums.')
        for album in tqdm(album_list):
            get_song_info(album)
    except KeyError:
        print("An Key exception occurred")

if __name__ == '__main__':
    # get main dataframe of mylist
    fetch_all(1000)
    mylist  = pd.concat([pd.DataFrame.from_dict(song_artist).reset_index(drop=True),pd.DataFrame.from_dict(song_album).reset_index(drop=True)], axis=1)
    mylist['song_name'], mylist['song_popularity'], mylist['song_duration'], mylist['song_id'] = [song_name, song_popularity, song_duration,song_id]
    mylist1  = mylist.drop_duplicates().reset_index(drop=True)

    for song_id in tqdm(mylist1['song_id']):
        get_song_json(song_id)

    for artist_id in tqdm(mylist1['artist_id']):
        get_artist_json(artist_id)

    get_artist_info(artist_detail_list)

    #select useful attributes   
    audio_df = pd.DataFrame.from_dict(audio_list)[['danceability', 
                                                'energy', 
                                                'key', 
                                                'loudness', 
                                                'mode', 
                                                'speechiness', 
                                                'acousticness', 
                                                'instrumentalness',
                                                'liveness', 
                                                'valence', 
                                                'tempo', 
                                                'type', 
                                                'id', 
                                                'uri', 
                                                'track_href', 
                                                'analysis_url', 
                                                'time_signature']]

    mylist1 = mylist1.merge(audio_df, left_on = 'song_id', right_on = 'id', how= 'left')
    mylist1['genres'] = artist_genres
    mylist1['follower'] = artist_follower 

    # to excel or DB
    mylist1.to_excel('songlist.xlsx')