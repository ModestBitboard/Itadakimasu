import argparse
import sys
import os
import json

from pathlib import Path

from utils import AppExit

# Some special values
__title__ = "Itadakimasu"
__version__ = "1.2.1"
__credit__ = "Built by Bitboard, 2025."
__summary__ = "A powerful client for watching anime from the Breadbox archive, built to be a safe haven for nerds."

# Exclude incompatible platforms
if sys.platform == 'win32':
    raise RuntimeError(f"{__title__} v{__version__} is incompatible with Windows.")
elif sys.platform == 'darwin':
    raise RuntimeError(f"{__title__} v{__version__} is incompatible with macOS.")

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-x', action='store_true', help="Run as a desktop application")
options = parser.parse_args()

# Load config
if XDG_CONFIG_HOME := os.environ.get('XDG_CONFIG_HOME'):
    config_file = Path(XDG_CONFIG_HOME) / 'breadbox' / 'config.json'
else:
    config_file = Path('~').expanduser() / '.config' / 'breadbox' / 'config.json'

if not config_file.parent.is_dir():
    config_file.parent.mkdir()

config = {}

if not config_file.is_file():
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
else:
    with open(config_file, 'r') as f:
        config = json.load(f)

# If running in desktop mode,
if options.x:
    print("Itadakimasu doesn't have a desktop app yet. :(")
else:
    from cli import App


# Set up the application
app = App(
    title=__title__,
    version=__version__,
    credit=__credit__,
    summary=__summary__,
    config=config
)

# Run the app
try:
    app.run()
except AppExit:
    pass

# Save any changes made to the config
with open(config_file, 'w') as f:
    json.dump(app.config, f, indent=2)
