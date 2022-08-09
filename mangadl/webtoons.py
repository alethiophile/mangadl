#!/usr/bin/python3

import urllib.request
from bs4 import BeautifulSoup
from .util import tosoup

def get_pages(url):
    soup = tosoup(url)
    elem = soup.find('div', id='_imageList')
    for i in elem('img'):
        yield i['data-url']

def get_chapters(url):
    soup = tosoup(url)
    elem = soup.find('h1', class_='subj')
    elem.div.decompose()
    title = elem.get_text()
    clist = []
    while True:
        elem = soup.find('ul', id='_listUl')
        for i in elem('li'):
            curl = i.a['href']
            st = i.find('span', class_='subj').get_text()
            clist.append((curl, st))
        try:
            nurl = soup.find('div', class_='paginate').find('a', onclick=True).find_next_sibling('a')['href']
        except:
            break
        nurl = 'http://www.webtoons.com' + nurl
        soup = tosoup(nurl)
        print("Processing {}".format(nurl))
    return title, list(reversed(clist))
