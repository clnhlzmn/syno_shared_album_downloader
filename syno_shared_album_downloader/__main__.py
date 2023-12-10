from sys import argv, exit

from .download import download

if __name__ == "__main__":
    try:
        download(argv[1], argv[2])
        exit(0)
    except Exception as e:
        print(e)
        exit(-1)
