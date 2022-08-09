#!/usr/bin/python3

from .trashscanlations import TrashScanlations
from .batoto import Batoto
from .mangadex import Mangadex
from .util import to_filename, sessionget
import click, trio, asks, urllib.parse, os, zipfile, re, qtoml

backend_res = [
    ( 'trashscanlations',
      re.compile("^https://trashscanlations.com/")),
    ( 'batoto',
      re.compile("^https://bato.to/")),
    ( 'mangadex',
      re.compile("^https://mangadex.org/")),
]

backend_objs = {
    'trashscanlations': TrashScanlations,
    'batoto': Batoto,
    'mangadex': Mangadex,
}

def find_backend(url):
    for name, pattern in backend_res:
        if pattern.match(url):
            return name
    raise ValueError(f"Couldn't find backend for URL '{url}'")

async def cbz_writer(recv_channel, fn):
    recvd = {}
    written = 0
    async with recv_channel:
        zipf = zipfile.ZipFile(fn, 'w')
        async for i in recv_channel:
            recvd[i[0]] = i
            while written in recvd:
                o = recvd.pop(written)
                img_fn = f"{o[0]:03}.{to_filename(o[1])}"
                zipf.writestr(img_fn, o[2])
                print(f"write #{o[0]} {img_fn}")
                written += 1
        zipf.close()

async def img_fetcher(dls, send_channel, ind, img_url):
    r = await sessionget(img_url)
    img = r.content
    parts = urllib.parse.urlparse(img_url)
    async with send_channel:
        ts = (ind, os.path.basename(parts.path), img)
        print(f"fetch #{ind} {img_url}")
        await send_channel.send(ts)
        dls.release_on_behalf_of(ind)

async def fetch_chapter(title_fn, cbz_fn, cle, il):
    async with trio.open_nursery() as nursery:
        send_channel, recv_channel = trio.open_memory_channel(3)
        # limit total downloads, to keep from having to cache too much before
        # writing to disk
        dls = trio.CapacityLimiter(10)
        async with send_channel, recv_channel:
            nursery.start_soon(cbz_writer, recv_channel.clone(), cbz_fn)
            for n, i in enumerate(il):
                await dls.acquire_on_behalf_of(n)
                nursery.start_soon(img_fetcher, dls, send_channel.clone(),
                                   n, i)

async def trio_main(url, num_chapters, dry_run):
    update_file = False
    fetched_data = {}
    if os.path.exists(url):
        update_file = True
        with open(url) as inp:
            fetched_data = qtoml.load(inp)

    real_url = (fetched_data['url'] if update_file else url)
    print(f"Fetching URL {real_url}")

    backend_name = (fetched_data['backend'] if update_file else
                    find_backend(url))
    handler = backend_objs[backend_name]()

    title, cl = await handler.get_chapters(real_url)
    title_fn = (fetched_data['title_fn'] if update_file else
                to_filename(title))

    update_fn = (url if update_file else f"{title_fn}.toml")

    if os.path.exists(update_fn):
        update_file = True
        with open(update_fn) as inp:
            fetched_data = qtoml.load(inp)

    if not update_file:
        fetched_data = { 'title': title, 'title_fn': title_fn, 'url': url,
                         'backend': backend_name, 'chapter_urls': {} }

    if dry_run:
        print(title)
        print(cl)
        il = await handler.get_pages(cl[0][1])
        print(il)
        return

    n_fetched = 0
    for n, c in enumerate(cl):
        if c[1] in fetched_data['chapter_urls']:
            if os.path.exists(fetched_data['chapter_urls'][c[1]]):
                print(f"Already have chapter {c[0]}")
                continue
            elif fetched_data['chapter_urls'][c[1]] == 'SKIP':
                print(f"Chapter {c[0]} marked for skipping")
                continue
        cbz_fn = f"{title_fn}.{n:03}.{to_filename(c[0])}.cbz"
        print(f"Fetching chapter {c[0]}")
        il = await handler.get_pages(c[1])
        await fetch_chapter(title_fn, cbz_fn, c, il)
        fetched_data['chapter_urls'][c[1]] = cbz_fn
        n_fetched += 1
        if num_chapters is not None and n_fetched >= num_chapters:
            break

    with open(update_fn, 'w') as out:
        qtoml.dump(fetched_data, out)

@click.command()
@click.option('--num-chapters', '-n', type=int,
              help="Number of chapters to fetch (default all)")
@click.option("--dry-run", type=bool, is_flag=True,
              help="Don't download, just test backend")
@click.argument('url', type=str)
def main(url, num_chapters, dry_run):
    asks.init('trio')
    trio.run(trio_main, url, num_chapters, dry_run)
