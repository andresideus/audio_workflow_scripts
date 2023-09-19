#!/bin/bash

# Check if virtual environment exists
if [ ! -d "python_env" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv python_env
    source python_env/bin/activate
    pip install -r requirements.txt
else
    echo "Virtual environment found."
    source python_env/bin/activate
fi

if ! xcode-select -p > /dev/null 2>&1 ; then
    xcode-select --install
else
    echo "Xcode Command Line Tools installed."
fi

# Run the Python script
pip install -r requirements.txt --quiet;\
python3 ./process_audio_files.py
