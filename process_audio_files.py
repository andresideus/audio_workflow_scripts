import os
import shutil
import yaml
import time
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
            for key in ['sd_card_path', 'google_drive_folder_id', 'service_json_path']:
                if key in config:
                    config[key] = os.path.expanduser(config[key])
            return config
        except yaml.YAMLError as exc:
            print(exc)
            return None

def play_slate(audio_path, slate_length):
    audio_data, samplerate = sf.read(audio_path, dtype='float32')
    num_frames = int(slate_length * samplerate)
    audio_data = audio_data[:num_frames]
    print(f"Playing {audio_path}, sample rate: {samplerate}.")
    sd.play(audio_data, samplerate=samplerate)
    sd.wait()

def push_to_google_drive(file_path, new_filename, folder_id, config):
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = Credentials.from_service_account_file(config['service_json_path'], scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        media = MediaFileUpload(file_path, mimetype='audio/wav', resumable=True)
        request = service.files().create(media_body=media, body={
            'name': new_filename,
            'parents': [folder_id]
        })
        
        print(f"Uploading {file_path} as {new_filename}.")
        file = request.execute()
        print(f"Uploaded {file['name']} to Google Drive.")

    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
def main():
    config = load_config()
    if not config:
        print("Error loading config file.")
        return
    
    last_fxname = None
    fxname_increment = 1
    
    ignore_folders = ['F6_SETTINGS', 'FALSE TAKE', 'TRASH']
    folders_to_delete = []

    for root, dirs, files in os.walk(config['sd_card_path']):
        if any(ignore in root for ignore in ignore_folders):
            continue
        
        wav_files = [f for f in files if f.endswith(".WAV")]
        
        if wav_files:
            first_wav_file = wav_files[0]
            full_path = os.path.join(root, first_wav_file)
            play_slate(full_path, config['slate_length'])

            if last_fxname:
                print(f"Default fxname: {last_fxname} {fxname_increment + 1}")  # Incremented by 1
            
            fxname = input("Enter fxname: ").strip()
            
            if not fxname:
                fxname = last_fxname
                fxname_increment += 1
            else:
                last_fxname = fxname
                fxname_increment = 1
            
            for wav_file in wav_files:
                parts = wav_file.split('_')
                date = parts[0]
                increment = parts[1]
                track_info = '_'.join(parts[2:]).replace('.WAV', '')

                mic_key = track_info.replace(".", "").replace(" ", "")
                mic = config['mic'].get(mic_key, "UNKNOWN")

                new_filename = f"{fxname} {fxname_increment}_{config['creator_id']}_{config['source_id']}_{date}-{mic}.WAV"
                full_path = os.path.join(root, wav_file)
                push_to_google_drive(full_path, new_filename, config['google_drive_folder_id'], config)
                folders_to_delete.append(root)
    
    # Moved this section out of the inner for loop
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
