#!/usr/bin/env bash

# For simplicity
base_path="/home/bitboard/Documents/Projects/Itadakimasu"

# Activate the virtual environment
. "$base_path/.venv/bin/activate"

# Start the tool
python "$base_path/app.py"

# Deactivate the virtual environment
deactivate
