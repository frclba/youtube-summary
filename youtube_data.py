from googleapiclient.discovery import build
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

youtubeApiKey = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube","v3", developerKey=youtubeApiKey)

channelUsername= "UCQ4FNww3XoNgqIlkBqEAVCg"
channelStats = youtube.channels().list(part = "snippet,contentDetails,statistics", id=channelUsername).execute()

channelStatistics = channelStats["items"][0]["statistics"]


channelStats = youtube.channels().list(part = "snippet,contentDetails,statistics", id=channelUsername).execute()
allUploadedVideosPlaylist =  channelStats["items"][0]['contentDetails']['relatedPlaylists']['uploads']


next_page_token = None

playlistData = youtube.playlistItems().list(playlistId=allUploadedVideosPlaylist,
                                               part='snippet',
                                               maxResults=50,
                                               pageToken=next_page_token).execute()

videos = [ ]

while True:
    playlistData = youtube.playlistItems().list(playlistId=allUploadedVideosPlaylist,
                                               part='snippet',
                                               maxResults=50,
                                               pageToken=next_page_token).execute()
    videos += playlistData['items']
    next_page_token = playlistData.get('nextPageToken')

    if next_page_token is None:
        break

video_ids=[]

for i in range(len(videos)):
    video_ids.append(videos[i]["snippet"]["resourceId"]["videoId"])
    i+=1

videoStatistics = []

for i in range(len(video_ids)):
    videoData = youtube.videos().list(id=video_ids[i],part = "statistics").execute()
    videoStatistics.append(videoData["items"][0]["statistics"])
    i+=1


VideoTitle=[ ]
url=[ ]
description=[ ]
Published = [ ]
Views=[ ]
LikeCount=[ ]
DislikeCount=[ ]
Comments=[ ]

for i in range(len(videos)):
    VideoTitle.append((videos[i])['snippet']['title'])
    url.append("https://www.youtube.com/watch?v="+(videos[i])['snippet']['resourceId']['videoId'])
    description.append((videos[i])['snippet']['description'])
    Published.append((videos[i])['snippet']['publishedAt'])
    Views.append(int((videoStatistics[i])['viewCount']))
    LikeCount.append(int((videoStatistics[i])['likeCount']))
    if ("commentCount" in videoStatistics[i]):
        Comments.append(int((videoStatistics[i])['commentCount']))
    else:
        Comments.append(0)




data={"Video Title" : VideoTitle, "Video url" : url, "Description": description, "Published" : Published, "Views" : Views, "Like Count" : LikeCount, "Comments" : Comments}
df=pd.DataFrame(data)
df.to_csv("youtubeChannel.csv")



