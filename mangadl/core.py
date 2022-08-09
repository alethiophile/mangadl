#!/usr/bin/python3

from .trashscanlations import TrashScanlations
from .batoto import Batoto
from .mangadex import Mangadex
from .util import to_filename, sessionget
import click, trio, asks, urllib.parse, os, zipfile, re, qtoml, math
from pathlib import Path

from typing import Optional

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
    # Images may come in in arbitrary order depending on network delay; cache
    # them until all previous have arrived, then write all in order.
    recvd = {}
    written = 0
    tmp_fn = fn + ".part"
    async with recv_channel:
        zipf = zipfile.ZipFile(tmp_fn, 'w')
        async for i in recv_channel:
            recvd[i[0]] = i
            while written in recvd:
                o = recvd.pop(written)
                img_fn = f"{o[0]:03}.{to_filename(o[1])}"
                zipf.writestr(img_fn, o[2])
                print(f"write #{o[0]} {img_fn}")
                written += 1
        zipf.close()
        os.rename(tmp_fn, fn)

async def img_fetcher(dls, send_channel, ind, img_url):
    for i in range(5):
        r = await sessionget(img_url)
        if r.status_code == 200:
            break
    else:
        raise RuntimeError(f"Bad status: {r.status_code} on {img_url}")
    img = r.content
    parts = urllib.parse.urlparse(img_url)
    async with send_channel:
        ts = (ind, os.path.basename(parts.path), img)
        print(f"fetch #{ind} {img_url}")
        await send_channel.send(ts)
        dls.release_on_behalf_of(ind)

async def fetch_chapter(cbz_fn, il):
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

def num_digits(num_chapters):
    if num_chapters < 1000:
        return 3
    return math.ceil(math.log10(num_chapters + 1))

async def get_manifest(fn: Optional[Path], url, language):
    print(f"Fetching manifest URL {url}")

    backend_name = find_backend(url)
    handler = backend_objs[backend_name]()

    manga_title, cl = await handler.get_chapters(url)
    num_chapters = len(cl)
    title_fn = to_filename(manga_title)

    # Convert from old plugin protocol
    for i in range(len(cl)):
        if type(cl[i]) == tuple:
            title, chap_url = cl[i]
            cl[i] = { 'title': title, 'url': chap_url }

    if language:
        cl = [i for i in cl if 'language' not in i or
              i['language'] == language]

    if fn is not None:
        manifest_path = Path(fn)
    else:
        dir_path = Path(title_fn)
        if not dir_path.exists():
            dir_path.mkdir(mode=0o755)
        if not dir_path.is_dir():
            raise RuntimeError(f"{title_fn} an existing file?")
        manifest_path = dir_path / 'manifest.toml'
    if manifest_path.exists():
        new_path = manifest_path.with_name(manifest_path.name + '.old')
        manifest_path.replace(new_path)

    def make_cbz_fn(ind, chapter):
        d = num_digits(num_chapters)
        return f"{title_fn}.{ind:0{d}}.{to_filename(chapter['title'])}.cbz"

    for n, c in enumerate(cl):
        c['cbz_fn'] = make_cbz_fn(n, c)

    manifest_data = {
        'title': manga_title,
        'title_fn': title_fn,
        'url': url,
        'backend': backend_name,
    }

    if language is not None:
        manifest_data['language'] = language

    manifest_data['chapters'] = cl

    with manifest_path.open('w') as out:
        qtoml.dump(manifest_data, out, encode_none='None')

async def run_download(manifest, dry_run, download_num):
    handler = backend_objs[manifest['backend']]()

    if dry_run:
        print(manifest['title'])
        il = await handler.get_pages(manifest['chapters'][0]['url'])
        print(il)
        return

    n_fetched = 0
    for n, c in enumerate(manifest['chapters']):
        if c.get('skip', False):
            continue
        if os.path.exists(c['cbz_fn']):
            print(f"Already have chapter {c['cbz_fn']}")
            continue
        elif c['cbz_fn'] == 'SKIP':
            print(f"Chapter {c['cbz_fn']} marked for skipping")
            continue
        cbz_fn = c['cbz_fn']
        print(f"Fetching chapter {c['title']}")
        il = await handler.get_pages(c['url'])
        await fetch_chapter(cbz_fn, il)
        n_fetched += 1
        if download_num is not None and n_fetched >= download_num:
            break

async def trio_main(url, download_num, update, dry_run, language):
    update_file = False
    inp_fn = None
    fetched_data = {}
    if os.path.exists(url):
        p = Path(url)
        update_file = True
        if p.is_dir():
            inp_fn = p / 'manifest.toml'
        else:
            inp_fn = p
        with inp_fn.open() as inp:
            fetched_data = qtoml.load(inp)

    if (not update_file) or update:
        real_language = (language if language is not None
                         else fetched_data['language'] if 'language' in
                         fetched_data else None)
        real_url = (fetched_data['url'] if update_file else url)
        await get_manifest(inp_fn, real_url, real_language)
    else:
        if p.is_dir():
            os.chdir(p)
        await run_download(fetched_data, dry_run, download_num)

@click.command()
@click.option('--num-chapters', '-n', type=int,
              help="Number of chapters to fetch (default all)")
@click.option("--dry-run", type=bool, is_flag=True,
              help="Don't download, just test backend")
@click.option("--update", type=bool, is_flag=True,
              help="Update file from original URL")
@click.option("--language", type=str, help="Filter for this language only")
@click.argument('url', type=str)
def main(url, num_chapters, update, dry_run, language):
    asks.init('trio')
    trio.run(trio_main, url, num_chapters, update, dry_run, language)
