from http.cookiejar import MozillaCookieJar
from json import loads
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile
from urllib.parse import urlparse, ParseResult

import requests


def download(sharing_url: str, output_path: str):
    """This takes Synology Photos shared album url like
    https://<hostname>/mo/sharing/<sharing_id> and downloads
    all the album contents to the specified output path.
    Usage of the API was discovered from simply opening
    the shared link in a browser and looking at the requests."""
    parsed_url: ParseResult = urlparse(sharing_url)
    hostname = parsed_url.hostname
    sharing_id = parsed_url.path.split('/')[-1]
    api_url = f"https://{hostname}/mo/sharing/webapi/entry.cgi"
    output_path: Path = Path(output_path)
    with requests.Session() as session:
        cookies = MozillaCookieJar()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-SYNO-SHARING": sharing_id,
        }
        session.cookies = cookies

        # Getting the shared link gets the authorization cookie.
        response = session.get(sharing_url)

        # This gets some info about the album, notably the
        # number of photos it contains, and its name.
        response = session.post(
            api_url,
            headers=headers,
            data={
                "api": "SYNO.Foto.Browse.Album",
                "method": "get",
                "version": "4",
                "passphrase": sharing_id,
                "additional": '["sharing_info","flex_section","provider_count","thumbnail"]',
            },
        )

        response = loads(response.content.decode())
        item_count = response["data"]["list"][0]["item_count"]

        # This gets a list of info about the photos in the album.
        response = session.post(
            api_url,
            headers=headers,
            data={
                "api": "SYNO.Foto.Browse.Item",
                "method": "list",
                "version": "4",
                "additional": '["thumbnail","resolution","orientation","video_convert","video_meta","provider_user_id"]',
                "offset": "0",
                "limit": {item_count},
                "sort_by": "takentime",
                "sort_direction": "asc",
                "passphrase": sharing_id,
            },
        )

        response = loads(response.content.decode())
        item_ids = [item["id"] for item in response["data"]["list"]]

        # This downloads the photos from the album as a zip archive.
        response = session.post(
            api_url,
            headers=headers,
            data={
                "force_download": "true",
                "api": "SYNO.Foto.Download",
                "method": "download",
                "item_id": str(item_ids),
                "version": "2",
                "download_type": "source",
                "passphrase": sharing_id,
                "_sharing_id": sharing_id,
            },
        )

        # Finally, extract the archive contents to the output path
        output_path.mkdir(exist_ok=True, parents=True)
        with NamedTemporaryFile(delete=False) as archive_file:
            archive_file.write(response.content)
            archive_file.close()
            archive = ZipFile(archive_file.name)
            archive.extractall(output_path)
