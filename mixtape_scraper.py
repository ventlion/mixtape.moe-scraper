#!/usr/bin/python3
import requests
import string
import random
import time
import argparse
import os

from threading import Thread
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen


def args():
    global file_ext
    global arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog="""
Format Groups:
  all     - all formats
  common  - common formats
  media   - video, audio and pictures
  text    - text, configs and data
  archive - archive files

Examples:
  # scrape for common formats with 24 threads and proxies
  python3 mixtape_scraper.py -t 24 -p common

  # scrape for all formats with 12 threads
  python3 mixtape_scraper.py -t 12 all

  # scrape for .wav formats with 1 thread
  python3 mixtape_scraper.py .wav
""")

    parser.add_argument("-t", "--threads",
                        type=int, help="Number of threads to use")
    parser.add_argument("-p", "--proxy",
                        action="store_true", help="Use rotating proxies")
    parser.add_argument("-v", "--verbose",
                        action="store_true", help="Verbose output")
    parser.add_argument("formats", type=str,
                        nargs='+', help="File extensions to search for")
    arguments = parser.parse_args()

    file_ext = arguments.formats
    if "all" in file_ext:
        file_ext.remove("all")
        file_ext = file_ext + ["", ".wav", ".mp3", ".flac",
                               ".aif", ".m4a", ".opus", ".webm",
                               ".mp4", ".mkv", ".flv", ".vob",
                               ".gif", ".mpeg", ".avi", ".png",
                               ".jpg", ".jpeg", ".bmp", ".pdf",
                               ".txt", ".config", ".ini", ".json",
                               ".data", ".epub", ".chm", ".rar",
                               ".zip", ".tar.gz"]

    if "common" in file_ext:
        file_ext.remove("common")
        file_ext = file_ext + ["", ".wav", ".mp3", ".flac",
                               ".aif", ".webm", ".mp4", ".flv",
                               ".gif", ".png", ".jpg", ".jpeg",
                               ".txt", ".config", ".pdf", ".zip",
                               ".rar", ".tar.gz", ".bz2", ".gz", ".7z"]

    if "media" in file_ext:
        file_ext.remove("media")
        file_ext = file_ext + ["", ".wav", ".mp3", ".flac",
                               ".aif", ".webm", ".mp4", ".mkv",
                               ".flv", ".gif", ".png", ".jpg", ".jpeg"]

    if "text" in file_ext:
        file_ext.remove("text")
        file_ext = file_ext + ["", ".txt", ".config", ".ini",
                               ".json", ".data", ".log"]

    if "archive" in file_ext:
        file_ext.remove("archive")
        file_ext = file_ext + ["", ".rar", ".zip", ".tar.gz",
                               ".bz2", ".iso", ".gz", ".7z", ".pea"]

    if arguments.verbose:
        print("Scraping for:", end=" ")
        for n in range(len(file_ext)):
            print(file_ext[n], end=" ")
        print("\n", end="")

    file_ext = list(set(file_ext))


# Function to get list of proxies
def get_proxies():
    # Retrieve latest proxies
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent',
                           "User-Agent Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36")  # noqa
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip':  row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        })

    # Choose a random proxy
    proxy_index = random_proxy()
    proxy = proxies[proxy_index]

    for n in range(1, 100):
        req = Request('http://icanhazip.com')
        req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')

    # Every 10 requests, generate a new proxy
    if n % 10 == 0:
        proxy_index = random_proxy()
        proxy = proxies[proxy_index]

        # Make the call
        try:
            my_ip = urlopen(req).read().decode('utf8')
            print('#' + str(n) + ': ' + my_ip)
        except OSError:  # If error, delete this proxy and find another one
            del proxies[proxy_index]
            print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' deleted.')
            proxy_index = random_proxy()
            proxy = proxies[proxy_index]


# Retrieve a random index proxy (we need the index to delete it if not working)
def random_proxy():
    return random.randint(0, len(proxies) - 1)


# Generate the url to request to
def genUrl():
    global id
    char_set = string.ascii_lowercase   # Character set for the ID
    id = "".join(random.sample(char_set*5, 6))  # Num of characters to assign
    url = "".join(["https://my.mixtape.moe/", str(id)])  # Joining ID to URL
    return(url)


def scraper():
    while True:
        url_to_test = str(genUrl())  # Generate a URL to test
        for format in file_ext:  # Test that URL for each format
            test_url = str(url_to_test + format)  # Adding file ext to the url
            time_now = str(time.strftime("%Y-%m-%d-%H.%M.%S"))
            filename = str("files/"
                           + time_now + " "
                           + id + format)  # Filename to write to if found
            if arguments.proxy:
                proxy_to_use = random.choice(proxies)
                # Requesting the URL
                filetest = requests.get(test_url, proxies=proxy_to_use)
                if arguments.verbose:
                    print("proxy: " + str(proxy_to_use))
            else:
                filetest = requests.get(test_url)  # Requesting the URL

            # If the URL is found, write to files/
            if "404" not in filetest.text:
                print("\033[0;32mFound file: \033[00m", test_url)
                with open(filename, "wb") as file:
                    file.write(filetest.content)
                break
            else:
                # If not found try a different URL
                print("\033[0;31mAttempted  "
                      + test_url + "\t\t"
                      + str(filetest)
                      + "\33[00m")


# ================ Main ================ #

args()  # Assigns arguments parsed
proxies = []  # Will contain proxies [ip, port]
get_proxies()  # Gets a list of proxies to use

if not os.path.exists("files"):
    os.makedirs("files")

# Start <threads> threads running scraper()
if arguments.threads:
    for i in range(arguments.threads):
        t = Thread(target=scraper)
        t.daemon = True
        t.start()
    t.join()
else:
    scraper()
