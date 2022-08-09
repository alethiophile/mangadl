#!python3

import urllib.parse, re
from pprint import pprint
from .util import sessionget
import datetime as dt

api_url = "https://api.mangadex.org"
data_url = "{}{}/{}"

title_re = re.compile(r"^https://mangadex.org/title/([0-9a-f-]+)/")
chapter_re = re.compile(r"^https://mangadex.org/chapter/([0-9a-f-]+)")

class Mangadex:
    async def get_chapters(self, url):
        o = title_re.match(url)
        if o is None:
            raise ValueError(f"bad Mangadex manga URL {url}")

        manga_id = o.group(1)

        r = await sessionget(f"{api_url}/manga/{manga_id}")
        if r.status_code >= 400:
            raise RuntimeError(f"request for {r.url} returned {r.status_code}")
        ro = r.json()

        # pprint(ro)

        manga_title = ro['data']['attributes']['title']['en']

        r = await sessionget(f"{api_url}/manga/{manga_id}/feed?"
                             "translatedLanguage[]=en&order[volume]=asc&"
                             "order[chapter]=asc")
        r.raise_for_status()
        co = r.json()

        # pprint(co)
        chapters = co['data']

        chapter_url = "https://mangadex.org/chapter/{}"

        rv = []
        for ch in chapters:
            e = ch['attributes']
            ctitle = f"Ch. {e['chapter']}" + (f" — {e['title']}" if e['title']
                                              else '')
            d = {
                'title': ctitle, 'url': chapter_url.format(ch['id']),
                'id': ch['id'], 'language': e['translatedLanguage'],
                'volume': int(e['volume'] if e['volume'] else 0),
                'chapter': float(e['chapter'] if e['chapter'] else 0),
                'date': dt.datetime.fromisoformat(e['updatedAt'])
            }
            rv.append(d)

        rv.sort(key=lambda x: x['chapter'])

        return manga_title, rv

        # soup = await tosoup(url)

        # te = soup.find('h6', class_='card-header')
        # manga_title = te.get_text().strip()

        # rv = []

        # page_list = []
        # pe = soup.find('div', class_='tab-content').find('nav')
        # for i in pe('a', class_='page-link'):
        #     try:
        #         link = urllib.parse.urljoin(url, i['href'])
        #         if link not in page_list:
        #             page_list.append(link)
        #     except KeyError:
        #         continue
        # # Remove the first entry, it's the "jump to first page" link with the
        # # data we already loaded
        # page_list = page_list[1:]

        # def get_cl(soup):
        #     el = soup.find('div', class_='chapter-container')
        #     for r in el('div', class_='row', recursive=False):
        #         cr = r.find('div', class_='chapter-row')
        #         try:
        #             cr['data-manga-id']
        #         except KeyError:
        #             continue
        #         te = r.find('a', class_='text-truncate')
        #         title = str(te.string)
        #         link = urllib.parse.urljoin(url, te['href'])

        #         le = r.find('div', class_='chapter-list-flag')
        #         language = le.img['title']

        #         ge = r.find('div', class_='chapter-list-group')
        #         translator = str(ge.a.string)

        #         yield {'title': title, 'url': link, 'language': language,
        #                'translator': translator}

        # rv.extend(get_cl(soup))
        # for i in page_list:
        #     s = await tosoup(i)
        #     rv.extend(get_cl(s))

        # rv.reverse()

        # return manga_title, rv

    async def get_pages(self, url):
        o = chapter_re.match(url)
        if o is None:
            raise ValueError(f"Bad Mangadex chapter URL {url}")

        chapter_id = o.group(1)

        r = await sessionget(f"{api_url}/at-home/server/{chapter_id}")
        if r.status_code >= 400:
            raise RuntimeError(f"request for {r.url} returned {r.status_code}")
        ro = r.json()

        bu = ro['baseUrl']
        hv = ro['chapter']['hash']

        def make_img_url(i):
            return f"{bu}/data/{hv}/{i}"

        rv = [make_img_url(i) for i in ro['chapter']['data']]
        return rv
