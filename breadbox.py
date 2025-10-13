import requests
import urllib3
import hashlib
import keyring
import io

from typing import Optional

# Metadata
__version__ = "1.0"

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Helper Exceptions
class APIKeyError(ValueError): """The API key is invalid or hasn't been set"""
class ServerNameError(ValueError): """The server hasn't been set"""

# User information helpers
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
    SERVER = None
    SERVICE_NAME = 'Breadbox'

    def __init__(self, base_url_override: str = None, api_key_override: str = None):
        if base_url_override:
            self.base_url = base_url_override
        elif Breadbox.SERVER:
            self.base_url = Breadbox.SERVER
        else:
            raise ServerNameError("You need to set a server")


        if api_key_override:
            self.api_key = api_key_override
        else:
            self.api_key = keyring.get_password(Breadbox.SERVICE_NAME, 'ApiKey')
            if not self.api_key:
                raise APIKeyError("You need to set an API key")

        self.user_id = get_user_id(self.api_key)

        self.anime = _AnimeArchive(self)
        #self.games = _GamesArchive(self)
        #self.linux = _LinuxArchive(self)

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

    @staticmethod
    def login(api_key: str):
        """
        Set the API key stored in the system keyring.
        """
        keyring.set_password(
            service_name=Breadbox.SERVICE_NAME,
            username='ApiKey',
            password=api_key
        )

    @staticmethod
    def logout():
        """
        Delete the API key from the system keyring.
        """
        keyring.delete_password(
            service_name=Breadbox.SERVICE_NAME,
            username='ApiKey'
        )

    @staticmethod
    def check_key(api_key: str) -> bool:
        """
        Check if an API key actually points to a user.
        """
        if not api_key:
            return False
        elif get_user_info(Breadbox.SERVER, get_user_id(api_key)):
            return True
        else:
            return False


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

    # noinspection PyShadowingBuiltins
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
