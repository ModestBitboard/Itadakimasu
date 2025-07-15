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

            if params['href'].startswith('magnet:?'):
                self.result['magnet'] = params['href']


class NyaaTorrent:
    """
    A torrent page on Nyaa.si
    """
    def __init__(self, nyaa_id: int):
        html = requests.get('https://nyaa.si/view/' + str(nyaa_id)).text
        parser = NyaaParser()
        parser.feed(html)

        self.magnet = parser.result['magnet']
