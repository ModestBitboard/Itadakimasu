"""
A simple library for getting information from nyaa.si
"""

from html.parser import HTMLParser
import requests

class NyaaParser(HTMLParser):
    """
    A simple parser for Nyaa.si

    https://www.reddit.com/r/Python/comments/v89fm9/is_it_possible_to_do_web_scraping_without_using/
    https://github.com/MadeOfMagicAndWires/qBit-plugins/blob/main/engines/nyaasi.py
    """
    def __init__(self):
        super().__init__()
        self.result = {}

    def handle_starttag(self, tag, attr):
        """Tell the parser what to do with which tags."""
        if tag == 'a':
            params = dict(attr)

            if (res := params['href']).startswith('magnet:?'):
                self.result['magnet'] = res

            elif (res := params['href']).endswith('.torrent'):
                self.result['torrent'] = res


class NyaaTorrent:
    """
    A torrent page on Nyaa.si
    """
    def __init__(self, nyaa_id: int):
        self.url = 'https://nyaa.si/view/' + str(nyaa_id)

        html = requests.get(self.url).text
        parser = NyaaParser()
        parser.feed(html)

        self.magnet = parser.result['magnet']
        self.file = 'https://nyaa.si' + parser.result['torrent']

    def download_file(self) -> bytes:
        """Fetch the contents of the .torrent file."""
        return requests.get(self.file).content

