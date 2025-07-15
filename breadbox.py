import requests
import urllib3
import hashlib
import io

from typing import Optional

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# User id helper
def get_user_id(api_key: str) -> int:
    """
    Extract a user's ID from their API key
    :return: The user's ID
    """
    return int(
        hashlib.sha256(
            api_key.encode()[:8]
        ).hexdigest()[:10],
        base=16
    )

def get_user_info(base_url: str, user_id: int) -> Optional[dict]:
    """
    Get information on a user
    :return: If user exists then return a dict, else None.
    """
    url = f"{base_url}/user/{user_id}"
    r = requests.get(url, verify=False)

    if r.status_code == 404:
        return None

    return r.json()


# Breadbox wrapper
class Breadbox:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.user_id = get_user_id(api_key)

        self.anime = _AnimeArchive(self)
        self.games = _GamesArchive(self)
        self.linux = _LinuxArchive(self)

    def fetch(self, relative_url, sign_url: bool = False, **kwargs):
        """
        Gets information, images, or media from Breadbox
        :param relative_url: The URL relative to breadbox
        :param sign_url: If true, return a signed URL pointing to the content instead of the content itself.
        Useful for interfacing with VLC.
        :return:
        """
        # Set up a requests session for Breadbox
        s = requests.Session()
        s.verify = False  # Disabled because Breadbox's certificate is self-signed.
        s.headers.update({'X-API-KEY': self.api_key})

        # Build URL
        url = self.base_url + relative_url

        if sign_url:
            url += '?signUrl'

        # Return the get request
        return s.get(url, **kwargs)

    def patch(self, relative_url, data: dict, **kwargs):
        """
        Uploads information to breadbox.
        :param relative_url: The URL relative to breadbox
        :param data: The data to upload
        :return:
        """

        # Set up a requests session for Breadbox
        s = requests.Session()
        s.verify = False  # Disabled because Breadbox's certificate is self-signed.
        s.headers.update({'X-API-KEY': self.api_key})

        # Build URL
        url = self.base_url + relative_url

        # Return the patch request
        return s.patch(url, json=data, **kwargs)

    def upload(self, relative_url, content: bytes, filename: str, mimetype: str, **kwargs):
        """
        Uploads a file to breadbox.
        :param relative_url: The URL relative to breadbox
        :param content: The file content to upload
        :param filename: The name of the file
        :param mimetype: The mimetype of the file
        :return:
        """

        # Set up a requests session for Breadbox
        s = requests.Session()
        s.verify = False  # Disabled because Breadbox's certificate is self-signed.
        s.headers.update({'X-API-KEY': self.api_key})

        # Build URL
        url = self.base_url + relative_url

        # IO
        file = io.BytesIO(content)

        # Return the put request
        return s.put(url, files={'file': (filename, file, mimetype)}, **kwargs)

    def user_info(self) -> Optional[dict]:
        """
        Get information on your user
        :return: If user exists then return a dict, else None.
        """
        return get_user_info(
            base_url=self.base_url,
            user_id=self.user_id
        )


# Abstract archive wrapper
class _AbstractArchive:
    def __init__(self, breadbox: Breadbox, name: str):
        self.breadbox = breadbox
        self.url_prefix = '/archive/' + name

    def fetch(self, relative_url: str, sign_url: bool = False, **kwargs):
        return self.breadbox.fetch(self.url_prefix + relative_url, sign_url, **kwargs)

    def patch(self, relative_url: str, data: dict, **kwargs):
        return self.breadbox.patch(self.url_prefix + relative_url, data, **kwargs)

    def upload(self, relative_url: str, content: bytes, filename: str, mimetype: str, **kwargs):
        return self.breadbox.upload(self.url_prefix + relative_url, content, filename, mimetype, **kwargs)

    def list_ids(self):
        return self.fetch('/').json()

    def info(self, id: int):
        return self.fetch('/' + str(id)).json()

    def all_info(self):
        return self.fetch('/all').json()

    def size(self):
        return self.fetch('/size').json()


# Populated archive wrappers

# noinspection PyShadowingBuiltins
class _AnimeArchive(_AbstractArchive):
    def __init__(self, breadbox: Breadbox):
        super().__init__(breadbox, 'anime')

    def list_media(self, id):
        return self.fetch('/' + str(id) + '/media').json()

    def get_media_url(self, id, media):
        return self.breadbox.base_url + self.fetch('/' + str(id) + '/media/' + str(media), sign_url=True).json()['url']

    def download_media(self, id, media):
        return self.fetch('/' + str(id) + '/media/' + str(media), stream=True)

# noinspection PyShadowingBuiltins
class _LinuxArchive(_AbstractArchive):
    def __init__(self, breadbox: Breadbox):
        super().__init__(breadbox, 'linux')

# noinspection PyShadowingBuiltins
class _GamesArchive(_AbstractArchive):
    def __init__(self, breadbox: Breadbox):
        super().__init__(breadbox, 'games')
