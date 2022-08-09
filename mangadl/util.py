#!/usr/bin/python3

import urllib.request, re, gzip
from bs4 import BeautifulSoup

def do_request(url, referer=None):
    hd = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0"}
    if referer:
        hd['Referer'] = referer
    req = urllib.request.Request(url, headers=hd)
    return urllib.request.urlopen(req)

def tosoup(url):
    #print(url)
    r = do_request(url)
    #print(r.getheaders())
    re = r.getheader('Content-Type')
    re = re[re.index('charset=')+8:]
    a = r.read()
    if r.getheader('Content-Encoding') == 'gzip':
        a = gzip.decompress(a)
    return BeautifulSoup(a, 'html5lib', from_encoding=re)

def to_filename(title):
    title = title.lower().replace(" ", ".")
    return re.sub("[^a-z0-9.]", "", title)
