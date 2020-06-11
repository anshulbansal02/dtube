from bs4 import BeautifulSoup as bs
import requests
from flask import Flask, jsonify, request
import time
import youtube_dl as yt

print(dir(yt))

def toSeconds(time):
    time = time.split(":")
    s = 0
    m = 1
    for t in reversed(time):
        s += int(t)*m
        m *= 60
    return s

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def parseUploadTime(date):
    if date == 'live':
        return ('live', 0)
    if not date:
        return ('upload', 0)

    t = date.split(' ')
    d = int(t[-3])

    if 'minute' in t[-2] or 'hour' in t[-2]:
        d = 0
    elif 'week' in t[-2]:
        d *= 7
    elif 'month' in t[-2]:
        d *= 30
    elif 'year' in t[-2]:
        d *= 365

    if t[0] == 'Streamed':
        return ('stream', d)
    else:
        return ('upload', d) 



def getContent(query, qtype):

    params = {
        "search_query": query,
        "sp": "EgIQAw%253D%253D" if qtype == 'playlist' else "EgIQAQ%253D%253D"
    }

    baseURL = "https://www.youtube.com/results/"
    response = requests.get(baseURL, params=params)

    if response.status_code != 200:
        raise HttpError

    soup = bs(response.content, 'html.parser')

    return soup




def extract_results(content):
    content_list = content.find('ol', class_="item-section")
    results = []

    if content_list:
        for card in content_list.find_all('div', class_="yt-lockup-tile"):
            if 'yt-lockup-video' in card['class']:
                results.append(parse_video(card))
            elif 'yt-lockup-playlist' in card['class']:
                results.append(parse_playlist(card))

    return results



def parse_playlist(playlist):
    channel = playlist.find('div', class_="yt-lockup-byline").a

    return {
        "type": "playlist",
        "playlist_url": playlist.find('a', class_="yt-pl-thumb-link")['href'].split('=')[-1],
        "title": playlist.find('h3', class_="yt-lockup-title").a.text,
        "channel_name": channel.text if channel else "",
        "channel_id": channel['href'].split('/')[-1] if channel else "",
        "video_count": playlist.find('span', class_="formatted-video-count-label").b.text,
        "playlist_thumbnail": playlist.find('div', class_="video-thumb").span.img['src'].split('?')[0]
    }


def parse_video(video):
    video_id = video['data-context-item-id']
    thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    duration_tag = video.find('span', class_="video-time")
    duration = toSeconds(duration_tag.text) if duration_tag else 0

    if duration_tag:
        duration = toSeconds(duration_tag.text)
        meta = video.find('ul', class_="yt-lockup-meta-info").find_all('li')
        if len(meta) > 1:
            upload_time = meta[0].text
            views = meta[1].text.split()[0].replace(',', '')
            views = int(views) if isInt(views) else 0
        else:
            upload_time = ""
            views = meta[0].text.split()[0].replace(',', '')
            views = int(views) if isInt(views) else 0
    else:
        duration = 0
        upload_time = 'live'
        views = video.find('ul', class_="yt-lockup-meta-info").li.text.split()[0]
        views = int(views.replace(',','')) if isInt(views) else 0

    title = video.find('h3', class_="yt-lockup-title").a.text
    channel = video.find('div', class_="yt-lockup-byline").a
    channel_name = channel.text
    channel_id = channel['href'].split('/')[-1]

    description_tag = video.find('div', class_="yt-lockup-description")
    description = description_tag.text if description_tag else ""

    return {
    "type": "video",
    "video_id": video_id,
    "thumbnail": thumbnail,
    "title": title,
    "duration": duration,
    "channel_name": channel_name,
    "channel_id": channel_id,
    "upload_time": upload_time,
    "views": views,
    "description": description
    }


def construct_search(query, vtype):

    t = time.time()

    if not query:
        return ({
            "time": (time.time()-t),
            "error": "Please provide a search string."
            })

    try:
        r = extract_results(getContent(query, vtype))

        return jsonify({
            "time": (time.time()-t),
            "item_count": len(r),
            "results": r
        })

    except Exception as ex:
        return ({
            "time": (time.time()-t),
            "error": ex
            })




app = Flask(__name__)

@app.route('/')
def index():
    return 'YT WEB CRAWLER'


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    vtype = request.args.get('t')
    return construct_search(query, vtype)


if __name__ == '__main__':
    app.run('192.168.0.110', 5000, debug=True)



