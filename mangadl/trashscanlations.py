#!python3

from .util import tosoup
import urllib.parse

class TrashScanlations:
    async def get_chapters(self, url):
        soup = await tosoup(url)
        el = soup.find('ul', class_='main')
        rv = []
        for i in el('li', class_='wp-manga-chapter'):
            title = i.a.string.strip()
            link = i.a['href']
            rv.append((title, link))
        rv.reverse()

        title = soup.find('div', class_='post-title').get_text().strip()
        return title, rv

    async def get_pages(self, url):
        parts = list(urllib.parse.urlparse(url))
        if not parts[2].endswith('/'):
            parts[2] += '/'
        parts[4] = 'style=list'
        url = urllib.parse.urlunparse(parts)

        soup = await tosoup(url)

        elem = soup.find('div', class_='read-container')
        rv = [i['src'] for i in
              elem('img', class_='wp-manga-chapter-img')]
        return rv
