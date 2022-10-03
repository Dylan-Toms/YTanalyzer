import sys
import yaml
import json as j
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import numpy

s = requests.Session()
s.verify = False
requests.packages.urllib3.disable_warnings()
retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[ 500, 502, 503, 504 ])
s.mount('https://', HTTPAdapter(max_retries=retries))

key = yaml.load(open('key.yml'), Loader=yaml.FullLoader)
ytAPI_key = key['youtube_apikey']
ytAPI = "https://www.googleapis.com/youtube/v3/"
maxResults = 10

file = open(r"data.csv", 'w')

# Get channelID from source of youtube page
def getSingleID(url):
    d = requests.get(url)
    page_source = d.content.decode('utf-8')
    channelID = page_source.split('channelId')[1].split('"')[2].replace('\\', '')
    return channelID

# Gets the channelID for a url from yml file
def getChannelIDs():
    channels = yaml.load(open('youtubers.yml'), Loader = yaml.FullLoader)['channels']
    channelIDs = []
    for v_url in channels:
        channelIDs.append(getSingleID(v_url))
    return channelIDs

# Returns an array of videoids
def getVideoIDs(channelid):
    url = '{}{}{}{}{}{}{}'.format(ytAPI, 'search?key=', ytAPI_key, '&channelId=', channelid, '&part=snippet,id&order=date&maxResults=', maxResults)
    videos = s.get(url).json()
    videoIDs = []
    for video in videos['items']:
        videoIDs.append(video['id']['videoId'])
    return videoIDs

# Get views for a video
def getViews(videoid):
    url = '{}{}{}{}{}'.format(ytAPI, 'videos?part=statistics&id=', videoid, '&key=', ytAPI_key)
    videos = s.get(url).json()
    return int(videos['items'][0]['statistics']['viewCount'])

# Adds data to the data.csv file
def getData():
    header = "url,"
    for i in range(maxResults):
        header += "view" + str(i + 1) + ","
    header += "cpm"
    file.write(header + '\n')
    for channel in getChannelIDs():
        line = "https://www.youtube.com/channel/" + channel + ","
        views = []
        for video in getVideoIDs(channel):
            viewcount = getViews(video)
            line += str(viewcount) + ","
            views.append(viewcount)
        values = numpy.array(views)
        mean = numpy.mean(values, axis = 0)
        sd = numpy.std(values, axis = 0)
        final_list = [x for x in views if (x > mean - 2 * sd)]
        final_list = [x for x in final_list if (x < mean + 2 * sd)]
        line += str(getCPM(final_list))
        file.write(line + "\n")
    file.close()


# Calcs the cost
def getCPM(views):
    CPM = ((sum(views) / len(views)) / 1000) * 20
    return CPM



# MAIN
def main():
    getData()


if __name__== "__main__":
  main()
