import os
import shutil
import yaml
import time
import numpy
import soundfile as sf
import sounddevice as sd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def load_config():
    print("Reading in config.")
    with open("config.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            
            # Expand any tildes (~) in paths
            if 'sd_card_path' in config:
                config['sd_card_path'] = os.path.expanduser(config['sd_card_path'])
            
            if 'google_drive_folder_id' in config:
                config['google_drive_folder_id'] = os.path.expanduser(config['google_drive_folder_id'])

            if 'service_json_path' in config:
                config['service_json_path'] = os.path.expanduser(config['service_json_path'])
                
            return config
        except yaml.YAMLError as exc:
            print(exc)

def play_first_5_seconds(audio_path):
    # Read the audio file into a numpy array
    audio_data, samplerate = sf.read(audio_path, dtype='float32')

    # Calculate the number of frames for 5 seconds
    num_frames = int(5 * samplerate)

    # Truncate or pad the audio data to have exactly 'num_frames' frames
    audio_data = audio_data[:num_frames]
    
    # Play the audio data
    print(f"Playing {audio_path}, sample rate: {samplerate}.")
    sd.play(audio_data, samplerate=samplerate)
    sd.wait()

def push_to_google_drive(file_path, new_filename, folder_id, config):
        
    try:
        # Initialize the Drive v3 API
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = None

        creds = Credentials.from_service_account_file(
            config['service_json_path'],
            scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=creds)

        # Upload file to Google Drive
        media = MediaFileUpload(file_path, mimetype='audio/wav')
        
        request = service.files().create(
            media_body=media,
            body={
                'name': new_filename,  # Using the new filename
                'parents': [folder_id]  # ID of the folder you want to upload to
            }
        )
        print(f"Uploading {file_path} as {new_filename}.")
        file = request.execute()
        print(f"Uploaded {file['name']} to Google Drive.")

    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
        print(f"Args: {e.args}")
    except Exception as e:
        print(f"An unknown error occurred: {e}")

def main():
    config = load_config()
    if not config:
        print("Error loading config file.")
        return

    ignore_folders = ['F6_SETTINGS', 'FALSE_TAKE', 'TRASH']  # Add folder names to ignore here
    folders_to_delete = []
    for root, dirs, files in os.walk(config['sd_card_path']):
        # Skip ignored folders
        if any(ignore in root for ignore in ignore_folders):
            continue

        wav_files = [f for f in files if f.endswith(".WAV")]
        if wav_files:
            first_wav_file = wav_files[0]
            full_path = os.path.join(root, first_wav_file)
            play_first_5_seconds(full_path)

            label = input("Enter label: ")

            for wav_file in wav_files:
                new_filename = f"{label}_placeholder_{wav_file}"  # TODO: Update your filename structure as needed
                full_path = os.path.join(root, wav_file)
                push_to_google_drive(full_path, new_filename, config['google_drive_folder_id'], config)
                folders_to_delete.append(root)

    # Ask to delete folders
    delete_folders = input("Do you want to delete processed folders? (yes/no): ").strip().lower()
    if delete_folders == 'yes':
        folders_to_delete = list(set(folders_to_delete))
        for folder in folders_to_delete:
            if not any(ignore in folder for ignore in ignore_folders):
                try:
                    shutil.rmtree(folder)
                    print(f"Deleted folder: {folder}")
                except Exception as e:
                    print(f"Couldn't delete folder {folder}. Error: {e}")

if __name__ == "__main__":
    main()
