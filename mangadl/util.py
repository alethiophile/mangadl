#!/usr/bin/python3

import re, asks
from bs4 import BeautifulSoup

web_session = None

async def sessionget(url, **kwargs):
    global web_session
    if web_session is None:
        web_session = asks.Session(connections=5)
    return await web_session.get(url, retries=5, **kwargs)

async def tosoup(url):
    r = await sessionget(url)
    soup = BeautifulSoup(r.text, 'html5lib')
    return soup

def to_filename(title):
    title = title.lower().replace(" ", ".")
    return re.sub("[^a-z0-9.]", "", title)
