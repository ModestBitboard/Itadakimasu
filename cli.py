from whiptail import Whiptail
from halo import Halo
from shutil import get_terminal_size
import requests
import subprocess
from pathlib import Path

from breadbox import Breadbox, APIKeyError
from utils import AppExit, Languages

# noinspection PyAttributeOutsideInit
class App:
    def __init__(self, title: str, version: str, credit: str, summary: str, config: dict):
        self.title = title
        self.version = version
        self.credit = credit
        self.summary = summary
        self.config = config

        self.backtitle = f" {self.title} v{self.version}"

        self.spinner = Halo(spinner='line', placement='right')
        self.breadbox: Breadbox

    def run(self):

        # Make sure all the important configurations exist
        if not self.config.get('server'):
            self.ask_for_server_url()

        # Set breadbox server
        Breadbox.SERVER = self.config['server']

        # Set up breadbox wrapper
        try:
            self.breadbox = Breadbox()

        except APIKeyError:
            self.ask_for_api_key()
            self.breadbox = Breadbox()

        self.spinner.start("Fetching user info...")

        # Get user info
        self.user_info = self.breadbox.user_info()

        self.spinner.stop()

        # Update backtitle to show user info
        self.backtitle = f" {self.title} v{self.version} | User: {self.user_info['username']}"

        # Load the main menu
        self.main_menu()

    def ask_for_server_url(self):
        inp = Whiptail(
            title="Breadbox",
            backtitle=self.backtitle
        ).inputbox(
            msg="The Breadbox server URL has not been set. Input it here and it will be saved automatically.\nUse Ctrl+Shift+V to paste.",
            default="https://api.example.com"
        )[0]

        if not inp:
            raise AppExit

        self.config['server'] = inp

    def ask_for_api_key(self):
        inp = Whiptail(
            title="Breadbox",
            backtitle=self.backtitle
        ).inputbox(
            msg="Your API key has not been set or is invalid. Input it here and it will be saved automatically.\nUse Ctrl+Shift+V to paste.",
            password=True
        )[0]

        if not inp:
            raise AppExit

        if not Breadbox.check_key(inp):
            self.ask_for_api_key()
        else:
            Breadbox.login(inp)

    def main_menu(self):
        inp = Whiptail(
            title="Breadbox",
            backtitle=self.backtitle
        ).menu("Welcome to Breadbox", [
            'Archive',
            'Settings',
            'Contribute',
            'About'
        ])[0]

        # noinspection PyUnreachableCode
        match inp:
            #case 'Archive': self.archive_menu()
            case 'Archive': self.anime_archive_menu()
            case 'Settings': self.settings_menu()
            case 'Contribute': self.contrib_menu()
            case 'About': self.about_menu()
            case _: raise AppExit

    def wip_message(self):
        Whiptail(
            title="Breadbox / ?",
            backtitle=self.backtitle
        ).msgbox("Unfortunately, there's nothing here yet. :(")

        self.main_menu()

    def archive_menu(self):
        inp = Whiptail(
            title="Breadbox / Archive",
            backtitle=self.backtitle
        ).menu("Select an archive:", [
            'Anime',
            'Games',
            'Linux'
        ])[0]

        # noinspection PyUnreachableCode
        match inp:
            case 'Anime': self.anime_archive_menu()
            case 'Games': ...
            case 'Linux': ...
            case _: self.main_menu()

    def settings_menu(self):
        self.wip_message()  # TODO: Settings menu

    def contrib_menu(self):
        if self.user_info['auth_level'] < 2:
            Whiptail(
                title="Breadbox / Contribute",
                backtitle=self.backtitle
            ).msgbox(
                "You lack the permissions required to make changes to the archive.\n"
                "\n"
                "Contact the archive's administrator for access if you'd like to make changes."
            )
            self.main_menu()

        inp = Whiptail(
            title="Breadbox / Contribute",
            backtitle=self.backtitle
        ).yesno(
            "You're about to be asked a series of questions. You can cancel at any time, but your work will be lost.\n"
            "\n"
            "Any contributions you make will either OVERWRITE existing information, or CREATE new information.\n"
            "Contributions cannot be undone.\n"
            "\n"
            "Continue?"
        )

        if not inp:
            self.main_menu()


        # ------ Anime ID ------
        inp = Whiptail(
            title="Breadbox / Contribute",
            backtitle=self.backtitle
        ).inputbox("What is the anime's ID on Breadbox?")[0]

        if not inp:
            self.main_menu()

        while not inp.isnumeric():
            Whiptail(
                title="Breadbox / Contribute",
                backtitle=self.backtitle
            ).msgbox("IDs must be numeric.")

            inp = Whiptail(
                title="Breadbox / Contribute",
                backtitle=self.backtitle
            ).inputbox("What is the anime's ID on Breadbox?")[0]

            if not inp:
                self.main_menu()

        breadbox_id = int(inp)
        page_title = "Breadbox / Contribute / " + inp


        # ------ Title ------
        inp = Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).inputbox("What is the anime's title?")[0]

        if not inp:
            self.main_menu()

        title = inp

        # ------ MyAnimeList ID ------
        inp = Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).inputbox("What is the anime's ID on MyAnimeList?")[0]

        if not inp:
            self.main_menu()

        while not inp.isnumeric():
            Whiptail(
                title=page_title,
                backtitle=self.backtitle
            ).msgbox("IDs must be numeric.")

            inp = Whiptail(
                title=page_title,
                backtitle=self.backtitle
            ).inputbox("What is the anime's ID on MyAnimeList?")[0]

            if not inp:
                self.main_menu()

        mal_id = int(inp)


        # ------ AniList ID ------
        inp = Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).inputbox("What is the anime's ID on AniList?")[0]

        if not inp:
            self.main_menu()

        while not inp.isnumeric():
            Whiptail(
                title=page_title,
                backtitle=self.backtitle
            ).msgbox("IDs must be numeric.")

            inp = Whiptail(
                title=page_title,
                backtitle=self.backtitle
            ).inputbox("What is the anime's ID on AniList?")[0]

            if not inp:
                self.main_menu()

        anilist_id = int(inp)


        # ------ Nyaa ID ------
        nyaa_ids = []

        while True:
            inp = Whiptail(
                title=page_title,
                backtitle=self.backtitle
            ).inputbox("What is the ID of the torrent on Nyaa.si?")[0]

            if not inp:
                self.main_menu()

            while not inp.isnumeric():
                Whiptail(
                    title=page_title,
                    backtitle=self.backtitle
                ).msgbox("IDs must be numeric.")

                inp = Whiptail(
                    title=page_title,
                    backtitle=self.backtitle
                ).inputbox("What is the ID of the torrent on Nyaa.si?")[0]

                if not inp:
                    self.main_menu()

            nyaa_ids.append(int(inp))

            if not Whiptail(
                title=page_title,
                backtitle=self.backtitle
            ).yesno(
                msg="Would you like to add another torrent?",
                default='no'
            ): break


        # ------ Audio ------
        inp = Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).checklist(
            "Select the languages that are available as audio.",
            Languages
        )[0]

        audio_languages = inp


        # ------ Subtitles ------
        inp = Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).checklist(
            "Select the languages that are available as subtitles.",
            Languages
        )[0]

        subtitle_languages = inp


        # ------ Confirm ------
        inp = Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).yesno(
            f"Title: {title}\n"
            f"Breadbox ID: {breadbox_id}\n"
            f"MyAnimeList ID: {mal_id}\n"
            f"AniList ID: {anilist_id}\n"
            f"Nyaa.si torrent IDs: [{', '.join(map(str, nyaa_ids))}]\n"
            f"Audio: [{', '.join(audio_languages)}]\n"
            f"Subtitles: [{', '.join(subtitle_languages)}]\n"
            "\n"
            "Any existing information will be lost!\n"
            "\n"
            "Continue?"
        )

        if not inp:
            self.main_menu()


        # ------ Find magnet link and torrent link ------
        self.spinner.start("Finding torrent info...")

        from nyaa import NyaaTorrent

        torrents = []

        for _id in nyaa_ids:
            torrent = NyaaTorrent(_id)

            torrents.append({
                "magnet": torrent.magnet,
                "file": torrent.file,
                "url": torrent.url
            })

        self.spinner.stop()


        # ------ Upload metadata ------
        self.spinner.start("Uploading metadata...")

        metadata = {
            "title": title,
            "audio": audio_languages,
            "subtitles": subtitle_languages,
            "external": {
                "myanimelist": f"https://myanimelist.net/anime/{mal_id}",
                "jikan": f"https://api.jikan.moe/v4/anime/{mal_id}",
                "anilist": f"https://anilist.co/anime/{anilist_id}"
            },
            "torrents": torrents
        }

        resp = self.breadbox.anime.patch('/' + str(breadbox_id), data=metadata).json()

        self.spinner.stop()

        Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).msgbox(
            f"{resp['details']}\n\nBreadbox response code: {resp['code']}"
        )

        self.spinner.start("Downloading thumbnail...")

        image_url = requests.get(f"https://api.jikan.moe/v4/anime/{mal_id}").json()['data']['images']['jpg']['image_url']

        resp = self.breadbox.anime.upload(
            f'/{breadbox_id}/thumbnail',
            content=requests.get(image_url).content,
            filename='thumbnail.jpg',
            mimetype='image/jpeg'
        ).json()

        self.spinner.stop()

        Whiptail(
            title=page_title,
            backtitle=self.backtitle
        ).msgbox(
            f"{resp['details']}\n\nBreadbox response code: {resp['code']}"
        )

        self.main_menu()

    def about_menu(self):
        Whiptail(
            title="Breadbox / About",
            backtitle=self.backtitle
        ).msgbox(f"{self.title} v{self.version}\n\n{self.summary}\n\n{self.credit}")

        self.main_menu()

    def anime_archive_menu(self):
        self.spinner.start("Fetching metadata...")

        # Get all anime info
        all_anime_info = self.breadbox.anime.all_info()

        # Calculate the size that the text inside the menu should be.
        sz = get_terminal_size().columns - 35

        # Create a list of whiptail options
        options = []
        for _id, _info in all_anime_info.items():
            # https://stackoverflow.com/a/2872519/19693227
            title = (_info['title'][:sz] + '..') if len(_info['title']) > sz else _info['title']
            options.append((_id, title))

        self.spinner.stop()

        # Ask the user which anime to watch
        inp = Whiptail(
            #title="Breadbox / Archive / Anime",
            title="Breadbox / Archive",
            backtitle=self.backtitle
        ).menu("Choose an anime to watch:", options)[0]

        # If the user cancelled; go back a menu.
        if not inp:
            #self.archive_menu()
            self.main_menu()

        self.anime_episode_menu(inp)

    def anime_episode_menu(self, anime_id):
        self.spinner.start("Fetching metadata...")

        media = self.breadbox.anime.list_media(anime_id)
        info = self.breadbox.anime.info(anime_id)

        episodes_info = requests.get(info['external']['jikan'] + '/episodes').json()['data']

        if len(media['episodes']) == 0:
            self.spinner.stop()
            Whiptail(
                title="Breadbox / " + info['title'],
                backtitle=self.backtitle
            ).msgbox(
                "This anime seems to be empty.\n"
                "\n"
                "Check back again later or contact the archive administrator."
            )
            self.anime_archive_menu()

        elif len(episodes_info) <= 1:
            self.anime_watch_menu(anime_id, '_movie')

        # Calculate the size that the text inside the menu should be.
        sz = get_terminal_size().columns - 32

        # Create a list of whiptail options
        options = []
        for _ep_num in media['episodes']:
            _ep_tit = episodes_info[_ep_num - 1]['title']
            # https://stackoverflow.com/a/2872519/19693227
            title = (_ep_tit[:sz] + '..') if len(_ep_tit) > sz else _ep_tit
            options.append((str(_ep_num), title))

        if len(media['bonus']) > 0:
            options.append(('*', 'Bonus'))

        self.spinner.stop()

        inp = Whiptail(
            title="Breadbox / " + info['title'],
            backtitle=self.backtitle
        ).menu("Choose an episode:", options)[0]

        if not inp:
            self.anime_archive_menu()

        elif inp == '*':
            inp = Whiptail(
                title="Breadbox / " + info['title'],
                backtitle=self.backtitle
            ).menu("Bonus content", media['bonus'])[0]

            if not inp:
                self.anime_episode_menu(anime_id)

        self.anime_watch_menu(anime_id, inp)

    def anime_watch_menu(self, anime_id, media_id):
        self.spinner.start("Fetching metadata...")

        info = self.breadbox.anime.info(anime_id)

        if media_id.isnumeric():
            ep_title = requests.get(info['external']['jikan'] + '/episodes').json()['data'][int(media_id) - 1]['title']
            msg = f"Episode {media_id} - {ep_title}"
        elif media_id == '_movie':
            msg = info['title'] + " - Movie"
        else:
            msg = "Bonus - " + media_id

        self.spinner.stop()

        inp = Whiptail(
            title="Breadbox / " + info['title'],
            backtitle=self.backtitle
        ).menu(msg, ['Stream with VLC', 'Save to downloads'])[0]

        if inp == 'Stream with VLC':
            url = self.breadbox.anime.get_media_url(anime_id, media_id)
            self.watch(url)

        elif inp == 'Save to downloads':
            self.spinner.start("Downloading media...")

            if not self.config.get('downloadFolder'):
                self.config['downloadFolder'] = '~/Downloads'

            downloads_folder = Path(self.config['downloadFolder']).expanduser()

            if media_id.isnumeric():
                filename = f"%s - Episode %02d.mp4" % (info['title'], int(media_id))
            else:
                filename = f"%s - %s" % (info['title'], media_id)

            file = downloads_folder / filename

            with open(file, 'wb') as fp:
                with self.breadbox.anime.download_media(anime_id, media_id) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=8192):
                        fp.write(chunk)

            self.spinner.stop()

            Whiptail(
                title="Breadbox / " + info['title'],
                backtitle=self.backtitle
            ).msgbox(f"Saved file to " + str(file))


        if media_id == '_movie':
            self.anime_archive_menu()
        else:
            self.anime_episode_menu(anime_id)

    @staticmethod
    def watch(url):
        subprocess.Popen(
            ['nohup', 'vlc', url],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL
        )
