from sys import argv, exit

from .download import download

if __name__ == "__main__":
    if len(argv) != 3:
        print("Usage python -m syno_shared_album_downloader <sharing url> <output path>")
        exit(-1)
    try:
        download(argv[1], argv[2])
        exit(0)
    except Exception as e:
        print(e)
        exit(-1)
