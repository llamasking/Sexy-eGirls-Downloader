#!/usr/bin/env python3
# Import things that will be needed.
import re
import sys
import json
import requests
from pathlib import Path
import multiprocessing

# Configuration
dlpath = "downloads/"

# Vars of the Gods
g_count = [ 0 , 0 ]
g_downloads = []

# Download function
def download(info):
    print("\r    - Downloading: " + info[0])

    dl = requests.get(info[1], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}, timeout=30, stream=True)
    length = int(dl.headers.get("content-length"))

    # Skip existing files
    if Path(info[0]).is_file() and Path(info[0]).stat().st_size == length:
        return

    if dl.status_code == 200:
        with open(info[0], "wb") as f:
            if length is None:
                f.write(dl.content)
            else:
                current = 0
                for data in dl.iter_content(chunk_size=4096):
                    current += len(data)
                    f.write(data)
                    # Progress bar
                    progress = current / length * 100
                    bar = "#" * int(progress / 2) + " " * int((100 - progress) / 2)
                    sys.stdout.write("\r      [%s] | %s/%s" % (bar, current, length))
                    sys.stdout.flush()
    else:
        print("      - ERROR! Status Code: " + dl.status_code)

# Create download path if it doesn't exist.
Path(dlpath).mkdir(parents=True, exist_ok=True)

# Input album URLs.
urls = []
while True:
    _input = input("Input album URL or leave blank to continue: ")
    if len(_input) != 0:
        urls.append(_input)
    else:
        break

# Just have a little break
print()

# Loop through each given url.
for albumURL in urls:
    print(">>> Querying API: " + albumURL, end="\n    - ")
    # Query album to get API url
    albumReq = requests.get(albumURL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}, timeout=30)

    # Check that album query worked.
    if albumReq.status_code != 200:
        # The 404 page on Sexy-Egirls actually responds with status code 200 so I don't think this'll ever fire.
        print("Error! Album request responded with status code " + str(albumReq.status_code))
        continue

    # Check that API url is in album response.
    apiURL = re.findall(r"https:\/\/www\.sexy-egirls\.com/api/v2/data\.php\?action=album-files.*token=[a-zA-Z0-9]*", albumReq.text, re.MULTILINE)
    if len(apiURL) != 1:
         print("Error! Album link does not contain API url. Maybe you entered a bad url?")
         continue

    # Query API.
    api = requests.get(apiURL[0], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}, timeout=30).json()

    # Check if API is happy.
    if not api['success']:
        # This probably won't ever happen.
        print("Error! API responded with a failure code.")
        continue

    # Count photos and videos
    imgs = 0
    vids = 0
    for i in api['files']:
        if i['type'] == "photo":
            imgs += 1
            g_count[0] += 1
        else:
            vids += 1
            g_count[1] += 1
    print("Success! Discovered " + str(imgs) + " images and " + str(vids) + " videos.")

    # Add album names and api response to lists
    g_downloads.append([albumURL.replace("https://www.sexy-egirls.com/albums/", ""), api['files']])

# Done querying API. Start downloading.
print("\n>>> Done querying API. Total: " + str(g_count[0]) + " images and " + str(g_count[1]) + " videos.")

# Loop through each album
for i in range(0, len(g_downloads)):
    # Create album folder
    Path(dlpath + g_downloads[i][0]).mkdir(parents=True, exist_ok=True)

    print("\n>>> Downloading album: " + g_downloads[i][0])

    # Loop through each image and build an array that looks like [["file", "img url"], ["file", "img url"]]
    dl_array = []
    for file in g_downloads[i][1]:
        # Filename is the same as on the CDN
        filename = re.findall(r"https://cdn1.sexy-egirls.com/cdn/girls/.*/(.*)", file["src"], re.MULTILINE)[0]

        # File is "download/<album>/<filename>"
        filename = dlpath + g_downloads[i][0] + "/" + filename

        # Add to array
        dl_array.append([filename, file["src"]])

    # Download one at a time
    for i in dl_array:
        download(i)