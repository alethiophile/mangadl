#!/usr/bin/python3

import urllib.request, urllib.parse, re
from bs4 import BeautifulSoup
from .util import tosoup

import multiprocessing

search_url = "http://www.batoto.net/search?name={name}&name_cond=c&p={page}"

def manga_search(string):
    """Takes a search string, pipes it through an in-site search engine, returns a
    list of search results.

    """
    rv = []
    page = 1
    while True:
        n = 0
        toget = search_url.format(name=urllib.parse.quote(string), page=page)
        soup = tosoup(toget)
        a = soup.find('div', id="comic_search_results")
        rl = a('tr', id=False, class_=False)
        for i in rl:
            u = i.find('a', href=re.compile(r"https?://"))
            u = u['href']
            t = i.find('strong').get_text()[1:]
            rv.append((u,t))
            n += 1
        if n < 30:
            break
        page += 1
    return rv

def get_chapters(url):
    """Takes a manga homepage URL, extracts the list of chapter URLs and other
    relevant metadata.

    """
    rv = []
    soup = tosoup(url)
    title = soup.find('h1', class_='ipsType_pagetitle').string.strip()
    t = soup.find('table', class_='chapters_list')
    try:
        rl = t('tr', class_='lang_English')
    except TypeError:
        print(soup.prettify())
        raise
    chaps = [[]]
    cnum = chaps[0]
    for i in rl:
        u = i.td.a['href']
        t = i.td.a.img.next_sibling[1:]
        g = i.find_all("td")[2].get_text().strip()
        try:
            c = float(re.search("ch([\d.]+)", u).group(1))
        except AttributeError:
            c = 0
        try:
            v = float(re.search("v([\d.]+)", u).group(1))
        except AttributeError:
            v = 0
        tu = (u,t,g,(v,c))
        if len(cnum) == 0 or cnum[0][3] == (v,c):
            cnum.append(tu)
        else:
            chaps.append([])
            cnum = chaps[-1]
            cnum.append(tu)
    chaps.reverse()
    sc = None
    for i in chaps:
        if len(i) == 1 or sc == None:
            # if sc != None and sc[2] != i[0][2]:
            #     print("switched to {} at {}".format(i[0][2], i[0][3]))
            sc = i[0]
            del i[1:]
            continue
        ll = [n for n in i if n[2] == sc[2]]
        if len(ll) == 0:
            ll = i
        i[0] = ll[0]
        sc = i[0]
        del i[1:]
    chaps = [i[0] for i in chaps]
    return title, [i[:2] for i in chaps]

def get_pages(url):
    """Takes a chapter URL, yields page image URLs. Because Batoto is fucking
    annoying, this requires O(n) page loads. I may have to find a different
    hosting site.

    """
    soup = tosoup(url)
    n = len(soup.find('select', id='page_select')('option'))
    yield soup.find('img', id='comic_page')['src']
    if url[-1] != '/':
        url += '/'
    for i in range(2,n+1):
        nu = url + str(i)
        soup = tosoup(nu)
        yield soup.find('img', id='comic_page')['src']

def get_pages_pool(url):
    """This doesn't work. Don't use it."""
    p = multiprocessing.Pool(4)
    soup = tosoup(url)
    n = len(soup.find('select', id='page_select')('option'))
    yield soup.find('img', id='comic_page')['src']
    def get_result(n):
        nu = url + str(n)
        soup = tosoup(nu)
        a = soup.find('img', id='comic_page')['src']
        print(a)
        return a
    for i in p.imap(get_result, range(2,n+1)):
        yield i
