#!/usr/bin/python3

import urllib.parse, re, json
from .util import tosoup

class Batoto:
    async def get_chapters(self, url):
        soup = await tosoup(url)
        el = soup.find('div', class_='chapter-list')
        rv = []

        def fix_title(t):
            return re.sub(r"\s+", " ", t).strip()

        for i in el('a', class_='chapt'):
            title = fix_title(i.get_text())
            link = urllib.parse.urljoin(url, i['href'])
            rv.append((title, link))
        rv.reverse()

        title = fix_title(soup.find('h3', class_='item-title').get_text())

        return title, rv

    async def get_pages(self, url):
        soup = await tosoup(url)
        elem = soup.find('script', string=re.compile(r"var images = \{"))
        o = re.search(r"var images = (\{[^}]+\})", elem.string)
        v = json.loads(o.group(1))
        rv = []
        for i in sorted(v.keys(), key=int):
            rv.append(v[i])
        return rv
