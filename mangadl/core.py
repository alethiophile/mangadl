#!/usr/bin/python3

from .trashscanlations import TrashScanlations
from mangadl.util import to_filename, sessionget
import click, trio, asks, urllib.parse, os, zipfile

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

async def img_fetcher(send_channel, ind, img_url):
    r = await sessionget(img_url)
    img = r.content
    parts = urllib.parse.urlparse(img_url)
    async with send_channel:
        ts = (ind, os.path.basename(parts.path), img)
        print(f"fetch #{ind} {img_url}")
        await send_channel.send(ts)

async def fetch_chapter(title_fn, ind, cle, il):
    cbz_fn = f"{title_fn}.{ind:03}.{to_filename(cle[0])}.cbz"
    async with trio.open_nursery() as nursery:
        send_channel, recv_channel = trio.open_memory_channel(3)
        async with send_channel, recv_channel:
            nursery.start_soon(cbz_writer, recv_channel.clone(), cbz_fn)
            for n, i in enumerate(il):
                nursery.start_soon(img_fetcher, send_channel.clone(),
                                   n, i)

async def trio_main(url):
    f = TrashScanlations()
    title, cl = await f.get_chapters(url)
    title_fn = to_filename(title)
    for n, c in enumerate(cl):
        print(f"Fetching chapter {c[0]}")
        il = await f.get_pages(c[1])
        await fetch_chapter(title_fn, n, c, il)

@click.command()
@click.argument('url', type=str)
def main(url):
    asks.init('trio')
    print(f"Fetching URL {url}")
    trio.run(trio_main, url)
