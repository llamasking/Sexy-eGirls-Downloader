# Import things that will be needed.
import re
import json
import requests
from time import time
from pathlib import Path
import multiprocessing

# Configuration
dlsync = True
dlthreads = 4
dlpath = "downloads/"

# Vars of the Gods
g_imgs = g_vids = 0
g_downloads = []

# Download function
def download(info):
    print("    - Downloading: " + info[0])
    dl = requests.get(info[1], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}, timeout=30)
    if dl.status_code == 200:
        open(info[0], "wb").write(dl.content)
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
        err_regex = re.findall(r"https:\/\/www\.sexy-egirls\.com\/albums\/(.*)", albumURL)
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
            g_imgs += 1
        else:
            vids += 1
            g_vids += 1
    print("Success! Discovered " + str(imgs) + " images and " + str(vids) + " videos.")

    # Add album names and api response to lists
    g_downloads.append([albumURL.replace("https://www.sexy-egirls.com/albums/", ""), api['files']])

# Done querying API. Start downloading.
print("\n>>> Done querying API. Total: " + str(g_imgs) + " images and " + str(g_vids) + " videos.")

# Loop through each album
for i in range(0, len(g_downloads)):
    # Create album folder
    Path(dlpath + g_downloads[i][0]).mkdir(parents=True, exist_ok=True)

    print("\n>>> Downloading album: " + g_downloads[i][0])

    # Loop through each image and build an array that looks like [["file", "img url"], ["file", "img url"]]
    dl_array = []
    for file in g_downloads[i][1]:
        # Filename is the same as on the CDN
        if file["type"] == "photo":
            filename = file["src"].replace("https://cdn1.sexy-egirls.com/cdn/girls/user-submissions", "")
        else:
            filename = file["src"].replace("https://cdn1.sexy-egirls.com/cdn/girls/videos", "")

        # File is "download/<album>/<filename>"
        filename = dlpath + g_downloads[i][0] + filename

        # Add to array
        dl_array.append([filename, file["src"]])

    # Download files
    if dlsync:
        # Download one at a time
        for i in dl_array:
            download(i)
    #else:
        # Download the files in parallel