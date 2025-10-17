import os
import sys
import json
import shutil
import requests
import subprocess
from pathlib import Path
from shutil import get_terminal_size

from whiptail import Whiptail
import questionary as q
from halo import Halo

from breadbox import Breadbox, APIKeyError


# Some metadata about the app
__title__ = "Itadakimasu"
__slug__ = "itadakimasu"
__version__ = "1.4.0"
__credit__ = "Built by Bitboard, 2025."
__summary__ = "A powerful client for watching anime from the Breadbox archive."

# Locate config
if XDG_CONFIG_HOME := os.environ.get('XDG_CONFIG_HOME'):
    config_root = Path(XDG_CONFIG_HOME) / __slug__
elif APPDATA := os.environ.get('APPDATA'):
    config_root = Path(APPDATA) / __slug__
else:
    config_root = Path('~').expanduser() / ('.' + __slug__)

config_file = config_root / 'config.json'
theme_folder = config_root / 'themes'

# Helper exception
class AppExit(Exception):
    """A tool for closing the app from anywhere within the app"""

# A helpful list of languages for the contribution tool
Languages = [
    'english',
    'japanese',
    'french',
    'spanish',
    'german',
    'italian',
    'chinese',
    'korean',
    'dutch',
    'finnish',
    'swedish',
    'norwegian',
    'danish',
    'russian',
    'arabic',
    'portuguese',
    'ukrainian',
    'polish',
]

# A handy dandy eraser
Eraser = '\x1b[1A\x1b[2K'

# Spawn a new detached instance of VLC
def vlc(media: str | list[str] | tuple[str], exit_after: bool = False):
    if sys.platform == 'win32':  # Experimental windows support
        args = ['start', '/b', '%ProgramFiles%\\VideoLAN\\VLC\\vlc.exe']
    else:
        args = ['nohup', 'vlc']

    if isinstance(media, (list, tuple)):
        args += media
    else:
        args.append(media)

    if exit_after:
        args.append('vlc://quit')

    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

# Main application class
# noinspection PyAttributeOutsideInit
class App:
    def __init__(self):
        self.title = __title__
        self.version = __version__
        self.credit = __credit__
        self.summary = __summary__

        # Declare config defaults
        self.default_config = {
            "server": None,
            "downloads_folder": "~/Downloads",
            "vlc_auto_exit": True,
            "enable_theme": True,
            "theme": "default"
        }

        self.config = self.default_config

        # Load configs if they exist; otherwise save defaults
        if config_file.is_file():
            self.load_config()
        else:
            self.save_config()

        # Set window background info
        self.backtitle = f" {self.title} v{self.version}"

        # Create spinner object
        self.spinner = Halo(spinner='line', placement='right', color="yellow")

        # Define other variables
        self.breadbox: Breadbox
        self.user_info: dict
        self.theme: dict

    def load_config(self):
        with open(config_file, 'r') as f:
            self.config = self.default_config | json.load(f)

    def save_config(self):
        # Create parent directory if it doesn't exist
        if not config_root.is_dir():
            config_root.mkdir()

        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def load_theme(self):
        """Load a custom whiptail theme"""
        # Create theme folder if it doesn't exist
        if not theme_folder.is_dir():
            shutil.copytree(Path(__file__).absolute().parent / 'themes', theme_folder)

        theme_file = theme_folder / (self.config['theme'] + '.json')
        with open(theme_file, 'r') as f:
            self.theme = json.load(f)

        t = self.theme

        root = f"{t['root_fg']},{t['root_bg']}"
        window = f"{t['window_fg']},{t['window_bg']}"
        element = f"{t['element_fg']},{t['element_bg']}"
        select = f"{t['select_fg']},{t['select_bg']}"
        focus = f"{t['focus_fg']},{t['focus_bg']}"

        # noinspection SpellCheckingInspection
        os.environ['NEWT_COLORS'] = f"""
            root={root}
            border={t['border']},{t['window_bg']}
            window={window}
            shadow={t['shadow']},{t['shadow']}
            title={t['window_title']},{t['window_bg']}
            button={focus}
            actbutton={focus}
            checkbox={element}
            actcheckbox={focus}
            entry={focus}
            label={window}
            listbox={element}
            actlistbox={select}
            textbox={window}
            acttextbox={focus}
            helpline={window}
            roottext={root}
            emptyscale={element}
            fullscale={focus}
            disentry={element}
            compactbutton={window}
            actsellistbox={focus}
            sellistbox={element}
        """

    def run(self):
        # Set Whiptail theme
        if self.config['enable_theme']:
            self.load_theme()

        # Make sure all the important configurations exist
        if not self.config.get('server'):
            self.ask_for_server_url()

        # Set breadbox server
        Breadbox.SERVER = self.config.get('server')

        # Set breadbox service name
        #Breadbox.SERVICE_NAME = __slug__

        # Set up breadbox wrapper
        try:
            self.breadbox = Breadbox()
        except APIKeyError:
            self.ask_for_api_key()
            self.breadbox = Breadbox()

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
            raise AppExit()

        self.config['server'] = inp
        self.save_config()

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
            # case 'Archive': self.archive_menu()
            case 'Archive':
                self.anime_menu()
            case 'Settings':
                self.settings_menu()
            case 'Contribute':
                self.contrib_menu()
            case 'About':
                self.about_menu()
            case _:
                raise AppExit

    # For development and debugging purposes
    def wip_message(self):
        Whiptail(
            title="Breadbox / ?",
            backtitle=self.backtitle
        ).msgbox("Unfortunately, there's nothing here yet. :(")

        self.main_menu()

    def anime_menu(self):
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
            title="Breadbox / Archive",
            backtitle=self.backtitle
        ).menu("Choose an anime to watch:", options)[0]

        # If the user cancelled; go back a menu.
        if not inp:
            self.main_menu()

        self.episode_menu(inp)

    def episode_menu(self, anime_id):
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
            self.anime_menu()

        elif len(episodes_info) <= 1:
            self.watch_menu(anime_id, '_movie')

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
            self.anime_menu()

        elif inp == '*':
            inp = Whiptail(
                title="Breadbox / " + info['title'],
                backtitle=self.backtitle
            ).menu("Bonus content", media['bonus'])[0]

            if not inp:
                self.episode_menu(anime_id)

        self.watch_menu(anime_id, inp)

    def watch_menu(self, anime_id, media_id):
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

            if not self.config.get('download_folder'):
                self.config['download_folder'] = '~/Downloads'

            downloads_folder = Path(self.config['download_folder']).expanduser()

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
            self.anime_menu()
        else:
            self.episode_menu(anime_id)

    def settings_menu(self):
        # Calculate the size that the text inside the menu should be.
        sz = get_terminal_size().columns - 42

        options = [
            ["server", "Set the Breadbox server address"],
            ["downloads_folder", "Set the destination for downloads"],
            ["vlc_auto_exit", "Enable/disable VLC closing after media is finished"],
            ["enable_theme", "Enable/disable custom Whiptail theme"],
            ["theme", "Set which whiptail theme is used"]
        ]

        # Automatically truncate larger options
        for opt in options:
            opt[1] = (opt[1][:sz] + '..') if len(opt[1]) > sz else opt[1]

        key = Whiptail(
            title="Breadbox / Settings",
            backtitle=self.backtitle
        ).menu(
            "Select the setting that you'd like to modify:",
            options
        )[0]

        if not key:
            self.main_menu()

        w = Whiptail(
            title="Breadbox / Settings / " + key,
            backtitle=self.backtitle
        )

        match key:
            case 'server':
                inp = w.inputbox(msg="Edit server URL:", default=self.config[key])[0]
                if inp:
                    self.config[key] = inp
            case 'downloads_folder':
                inp = w.inputbox(msg="Please provide a valid path:", default=self.config[key])[0]
                if inp:
                    self.config[key] = inp
            case 'vlc_auto_exit':
                if self.config[key]:
                    inp = w.yesno(msg="Disable VLC auto-exit?")
                    if inp:
                        self.config[key] = False
                else:
                    inp = w.yesno(msg="Enable VLC auto-exit?")
                    if inp:
                        self.config[key] = True
            case 'enable_theme':
                if self.config[key]:
                    inp = w.yesno(msg="Disable custom theme?")
                    if inp:
                        self.config[key] = False
                else:
                    inp = w.yesno(msg="Enable custom theme?")
                    if inp:
                        self.config[key] = True
            case 'theme':
                options = []
                for fil in theme_folder.iterdir():
                    if fil.is_file() and fil.suffix == '.json':
                        options.append(fil.stem)

                inp = w.menu("Current theme: " + self.config['theme'], options)[0]

                if inp:
                    self.config[key] = inp

                self.load_theme()

        self.save_config()
        self.settings_menu()

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

        image_url = requests.get(f"https://api.jikan.moe/v4/anime/{mal_id}").json()['data']['images']['jpg'][
            'image_url']

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

    def watch(self, url: str):
        vlc(url, exit_after=self.config['vlc_auto_exit'])


# Fallback application class
class FallbackApp(App):
    @staticmethod
    def erase_line():
        """Erase the last line written to stdout"""
        sys.stdout.write(Eraser)

    def ask_for_server_url(self):
        inp = q.text("Input a server URL:", default="https://api.example.com").ask(kbi_msg=Eraser)
        self.erase_line()

        if not inp:
            raise AppExit()

        self.config['server'] = inp
        self.save_config()

    def ask_for_api_key(self):
        inp = q.password("Set API key:").ask(kbi_msg=Eraser)
        self.erase_line()

        if not inp:
            raise AppExit

        if not Breadbox.check_key(inp):
            self.ask_for_api_key()
        else:
            Breadbox.login(inp)

    def main_menu(self):
        inp = q.select("Welcome to Breadbox", [
            'Archive',
            'About',
            'Exit'
        ]).ask(kbi_msg=Eraser)
        self.erase_line()

        match inp:
            case 'Archive':
                self.anime_menu()
            case 'About':
                self.about_menu()
            case _:
                raise AppExit

    # For development and debugging purposes
    def wip_message(self):
        q.press_any_key_to_continue("Unfortunately, there's nothing here yet. :(").ask(kbi_msg=Eraser)
        self.erase_line()
        self.main_menu()

    def anime_menu(self):
        self.spinner.start("Fetching metadata...")

        # Get all anime info
        all_anime_info = self.breadbox.anime.all_info()

        # Create a list of options
        options = []
        for _id, _info in all_anime_info.items():
            options.append(q.Choice(title=_info['title'], value=_id))

        options.append(q.Choice(title="<-----[ Back ]", value=False))

        self.spinner.stop()

        # Ask the user which anime to watch
        inp = q.select("Choose an anime to watch:", options).ask(kbi_msg=Eraser)
        self.erase_line()

        # If the user cancelled; go back a menu.
        if not inp:
            self.main_menu()

        self.episode_menu(inp)

    def episode_menu(self, anime_id):
        self.spinner.start("Fetching metadata...")

        media = self.breadbox.anime.list_media(anime_id)
        info = self.breadbox.anime.info(anime_id)

        episodes_info = requests.get(info['external']['jikan'] + '/episodes').json()['data']

        if len(media['episodes']) == 0:
            self.spinner.stop()
            q.press_any_key_to_continue("This anime seems to be empty.").ask(kbi_msg=Eraser)
            self.erase_line()
            self.anime_menu()

        elif len(episodes_info) <= 1:
            self.watch_menu(anime_id, '_movie')

        options = []
        for _ep_num in media['episodes']:
            _ep_tit = episodes_info[_ep_num - 1]['title']
            options.append(q.Choice(title=str(_ep_num) + ' - ' + _ep_tit, value=_ep_num))

        if len(media['bonus']) > 0:
            options.append(q.Choice(title="* - Bonus", value='*'))

        options.append(q.Choice(title="<-----[ Back ]", value=False))

        self.spinner.stop()

        inp = q.select("Choose an episode:", options).ask(kbi_msg=Eraser)
        self.erase_line()

        if not inp:
            self.anime_menu()

        elif inp == '*':
            inp = q.select("Bonus content:", [
                *media['bonus'],
                q.Choice(title="<-----[ Back ]", value=False)
            ]).ask(kbi_msg=Eraser)
            self.erase_line()

            if not inp:
                self.episode_menu(anime_id)

        self.watch_menu(anime_id, str(inp))

    def watch_menu(self, anime_id, media_id):
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

        inp = q.select(msg, [
            "Stream with VLC",
            "Save to downloads",
            "<-----[ Back ]"
        ]).ask(kbi_msg=Eraser)
        self.erase_line()

        if inp == 'Stream with VLC':
            url = self.breadbox.anime.get_media_url(anime_id, media_id)
            self.watch(url)

        elif inp == 'Save to downloads':
            self.spinner.start("Downloading media...")

            if not self.config.get('download_folder'):
                self.config['download_folder'] = '~/Downloads'

            downloads_folder = Path(self.config['download_folder']).expanduser()

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

            q.press_any_key_to_continue("Saved file to " + str(file)).ask(kbi_msg=Eraser)
            self.erase_line()


        if media_id == '_movie':
            self.anime_menu()
        else:
            self.episode_menu(anime_id)

    def about_menu(self):
        q.press_any_key_to_continue(self.backtitle).ask(kbi_msg=Eraser)
        self.erase_line()
        self.main_menu()

if __name__ == '__main__':

    # Check if whiptail is installed
    if shutil.which('whiptail'):
        app = App()
    else:
        app = FallbackApp()

    try:
        app.run()
    except AppExit:
        pass
