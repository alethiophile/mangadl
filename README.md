# mangadl

mangadl is a tool for downloading manga from manga viewer sites as CBZ files.

To use, check out the project, then enter its directory and issue:

```console
$ poetry install
(...)
$ poetry shell
$ mangadl --help
Usage: mangadl [OPTIONS] URL

Options:
  -n, --num-chapters INTEGER  Number of chapters to fetch (default all)
  --dry-run                   Don't download, just test backend
  --update                    Update file from original URL
  --language TEXT             Filter for this language only
  --help                      Show this message and exit.
```
