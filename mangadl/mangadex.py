#!python3

import urllib.parse, re
from pprint import pprint
from .util import sessionget
import datetime as dt

api_url = "https://mangadex.org/api/"
data_url = "{}{}/{}"

title_re = re.compile(r"^https://mangadex.org/title/(\d+)/")
chapter_re = re.compile(r"^https://mangadex.org/chapter/(\d+)")

class Mangadex:
    async def get_chapters(self, url):
        o = title_re.match(url)
        if o is None:
            raise ValueError(f"bad Mangadex manga URL {url}")

        manga_id = o.group(1)

        r = await sessionget(api_url, params={'id': manga_id, 'type': 'manga'})
        if r.status_code >= 400:
            raise RuntimeError(f"request for {r.url} returned {r.status_code}")
        ro = r.json()

        # pprint(ro)

        manga_title = ro['manga']['title']
        chapters = [i for i in sorted(ro['chapter'].keys(), key=int)]

        chapter_url = "https://mangadex.org/chapter/{}"

        rv = []
        for i in chapters:
            e = ro['chapter'][i]
            # pprint(e)
            ctitle = f"Ch. {e['chapter']}" + (f": {e['title']}" if e['title']
                                              else '')
            d = {
                'title': ctitle, 'url': chapter_url.format(i), 'id': i,
                'language': e['lang_code'], 'translator': e['group_name'],
                'volume': int(e['volume'] if e['volume'] else 0),
                'chapter': float(e['chapter'] if e['chapter'] else 0),
                'date': dt.datetime.fromtimestamp(e['timestamp'],
                                                  dt.timezone.utc),
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

        r = await sessionget(api_url,
                             params={'id': chapter_id, 'type': 'chapter'})
        if r.status_code >= 400:
            raise RuntimeError(f"request for {r.url} returned {r.status_code}")
        ro = r.json()
        # print(ro)

        def make_img_url(ro, i):
            u = data_url.format(ro['server'], ro['hash'], i)
            return urllib.parse.urljoin(url, u)

        rv = [make_img_url(ro, i) for i in ro['page_array']]
        return rv
