#!/usr/bin/python3

import mangadl.batoto as batoto
import mangadl.webtoons as webtoons
import mangadl.mangacow as mangacow
import multiprocessing, zipfile, os, sys
from multiprocessing import Queue, Process
from multiprocessing.sharedctypes import Value
from queue import Empty
from mangadl.util import to_filename, do_request
import urllib.request, mimetypes, argparse, json

manga_mod = None
mod_hosts = { 'bato.to': batoto,
              'www.webtoons.com': webtoons,
              'mngcow.co': mangacow }

def download_manga(url, update=False):
    """Takes a manga main-page URL, downloads the whole thing, creating a
    subdirectory named after the manga in the current directory, then storing
    chapter .cbz files in that directory.

    """
    global manga_mod
    # if 'www.webtoons.com' in url:
    #     manga_mod = webtoons
    for i in mod_hosts:
        if i in url:
            manga_mod = mod_hosts[i]
    if manga_mod is None:
        print("Error: no URL found", file=sys.stderr)
        sys.exit(1)
    if update:
        with open(os.path.join(url, 'update.json'), 'r') as f:
            a = json.load(f)
        mt = url
        if mt[-1] == '/':
            mt = mt[:-1]
        url = a['url']
        title, clist = manga_mod.get_chapters(url)
        ctd = [i for i in nc if i not in a['chapters']]
        print(ctd)
    else:
        title, clist = manga_mod.get_chapters(url)
        mt = to_filename(title)
        ctd = clist
    os.makedirs(mt, exist_ok=True)
    os.chdir(mt)
    print("{} chapters to get ({} total)".format(len(ctd), len(clist)))
    for n,i in enumerate(clist):
        print("Downloading chapter {}: {}".format(n+1, i[1]))
        download_chapter(i, mt)
    with open('update.json', 'w') as f:
        json.dump({'chapters': clist, 'url': url}, f)

def do_search(string):
    result = manga_mod.manga_search(string)
    print("Search results:")
    for i in result:
        print("{}: {}".format(i[1], i[0]))

def download_chapter(chap, mt=''):
    """Takes a tuple of (url, title) for a chapter, downloads the entire chapter,
    stores the contents as .cbz in the current directory. The parameter mt is
    the (already filename-adjusted) title of the manga as a whole; if present,
    it'll be prepended to the filename of the cbz.

    """
    if mt:
        fn = mt + '.' + to_filename(chap[1]) + '.cbz'
    else:
        fn = to_filename(chap[1]) + '.cbz'
    f = zipfile.ZipFile(fn, 'w')
    done = Value('B', 0, lock=False)
    sq = Queue()
    rq = Queue()

    def source_process(url, q, v):
        for i in enumerate(manga_mod.get_pages(url)):
            #print("sourcing {}".format(i))
            q.put(i)
        q.close()
        v.value = 1
    sp = Process(target=source_process, args=(chap[0], sq, done))
    sp.start()

    def dl_process(s, r, v):
        while True:
            try:
                a = s.get(timeout=0.5)
            except Empty:
                if v.value:
                    break
                else:
                    continue
            e = do_request(a[1], referer=chap[0])
            dt = e.getheader('Content-Type')
            fd = e.read()
            r.put((a[0], fd, dt))
            #print("getting {} in {}".format(a, multiprocessing.current_process().pid))
    dlp = [Process(target=dl_process, args=(sq, rq, done)) for i in range(4)]
    for i in dlp:
        i.start()

    while True:
        try:
            a = rq.get(timeout=0.5)
            print("page {}".format(a[0]+1), end='\r')
        except Empty:
            if not any([i.is_alive() for i in dlp]):
                break
            else:
                continue
        ext = mimetypes.guess_extension(a[2])
        #print(ext)
        if ext in [".jpeg", ".jpe"]:
            #print("change")
            ext = ".jpg"
        fn = "{:03}".format(a[0]) + ext
        #print(fn)
        f.writestr(fn, a[1])
        
    print('', end='\n')
    f.close()

def main():
    parser = argparse.ArgumentParser(description="A downloader for manga sites")
    parser.add_argument("-u", "--update", action="store_true", help="Update an existing download", default=False)
    parser.add_argument("-s", "--search", action="store_true", help="Search for a string", default=False)
    parser.add_argument("url", help="URL, directory, search term")
    a = parser.parse_args()

    if a.update and a.search:
        print("Error: -u and -s mutually exclusive", file=sys.stderr)
        sys.exit(1)

    if a.update:
        pass
    elif a.search:
        do_search(a.url)
    else:
        download_manga(a.url)

if __name__=="__main__":
    main()
