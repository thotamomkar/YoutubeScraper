from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
#from bs4 import BeautifulSoup as bs
#from urllib.request import urlopen as uReq
from googleapiclient.discovery import build
import pandas as pd

app = Flask(__name__)

api_key = '<YOUR API KEY here>'
youtube = build('youtube', 'v3', developerKey=api_key)

def get_channel_stats(youtube, channel_id):
    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        id=channel_id )
    response = request.execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    return playlist_id


def get_video_ids(youtube, playlist_id):
    request = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=playlist_id,
        maxResults=50)
    response = request.execute()

    video_ids = []

    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    more_pages = True

    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token)
            response = request.execute()

            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')

    return video_ids


def get_video_details(youtube, video_ids):
    all_video_stats = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part='id,snippet,statistics',
            id=','.join(video_ids[i:i + 50]))
        response = request.execute()

        for video in response['items']:
            video_stats = dict(Title=video['snippet']['title'],
                               URL='https://www.youtube.com/watch?v=' + (video['id']),
                               Views=video['statistics']['viewCount'],
                               Likes=video['statistics']['likeCount'],
                               Comments=video['statistics']['commentCount'],
                               Thumbnail=video['snippet']['thumbnails']['default']['url']
                               )
            all_video_stats.append(video_stats)

    return all_video_stats


@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/review',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:

            searchString = request.form['content']
            playlist_id = get_channel_stats(youtube, searchString)
            video_ids = get_video_ids(youtube, playlist_id)
            video_details = get_video_details(youtube, video_ids)

#            mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
#                          "Comment": custComment}
#            reviews.append(mydict)
            return render_template('results.html', reviews=video_details[0:(len(video_details)-1)])
        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
    # return render_template('results.html')

    else:
        return render_template('index.html')

if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=8001, debug=True)
	app.run(debug=True)
