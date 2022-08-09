#!/usr/bin/python3

import urllib.request
import os
from bs4 import BeautifulSoup
from .util import tosoup

def get_chapters(url):
    soup = tosoup(url)
    td = soup.find('div', class_='det')
    title = td.h4.string
    pl = soup.find('ul', class_='pgg')
    llist = []
    ulist = []
    for i in pl('a'):
        if i.string.isdigit() and i != '1':
            llist.append(str(i['href']))
    def soup_links(soup):
        l = soup.find('ul', class_='mng_chp')
        for i in l('li'):
            url = i.a['href']
            title = i.a.b.string
            ulist.append((url, title))
    #soup_links(soup)
    for i in llist:
        soup_links(tosoup(i))
    return title, list(reversed(ulist))

def get_pages(url):
    soup = tosoup(url)
    csel = soup.find('select', class_='cbo_wpm_pag')
    ccount = len(csel('option'))
    idiv = soup.find('div', class_='prw')
    iurl = idiv.find('img')['src']
    idir = os.path.dirname(iurl)
    rv = []
    for i in range(ccount):
        purl = url + str(i+1) + '/'
        s = tosoup(purl)
        iurl = s.find('div', class_='prw').a.img['src']
        #rv.append('{0}/{1:04d}.jpg'.format(idir, i))
        rv.append(iurl)
    return rv
