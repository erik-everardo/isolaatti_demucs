# Erik, last modified november 13, 2020
# demucs_host.py
# this program will always asking the server for a job, 
# if found one, this host will stop asking and process it

from threading import Thread, Event
from time import sleep
import requests
import config
from termcolor import colored
import os
import subprocess
import json
import uuid
from os import path
import API

import uuid
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from google.cloud import storage

pause = Event()
pause.set()

def request_job():
    while (True):
        pause.wait()
        print(colored("[this machine]","blue", attrs=["bold"]), "Requesting job...")
        response = API.get_job_from_queue()
        if response.status_code == requests.status_codes.codes["ok"]:
            print(colored("[server]","blue",attrs=["bold"]), colored("Job found!","green",attrs=["bold"]))
            parsedResponse = json.loads(response.text)
            # reserves the process, so that no other host takes it
            API.reserve_job_from_queue(parsedResponse["id"])
            print("reserving job")
            start_process(parsedResponse["userId"],parsedResponse["audioSourceUrl"],parsedResponse["songName"],parsedResponse["songArtist"])
        else:
            print(colored("[server]","blue",attrs=["bold"]),colored("No job!","red",attrs=["bold"]))
        sleep(10)
        if os.name == "posix":
            os.system ("clear")
        elif os.name == "ce" or os.name == "nt" or os.name == "dos":
            os.system ("cls")
    
def start_process(userId,url,songName, songArtist):
    # download the file
    destination = config.path_dir_dw_songs

    song_file = requests.get(url, allow_redirects=True)
    song_uid = uuid.uuid1()
    name = os.path.join(destination,"{}".format(song_uid))
    open(name,'wb').write(song_file.content)
    print("File has been downloaded to " + destination)
    print("Song information")
    print("Name: {}".format(songName))
    print("Artist: {}".format(songArtist))
    print("User id: {}".format(userId))

    # creates record in order to get an id on the database
    new_song_id = API.create_song_record(userId,songName,songArtist)

    # here the notification is sent by the API (Your song is being processed!)
    API.started_process(new_song_id)

    print(colored("[demucs_service]","blue"),"Here the job is being done...")

    # it's easier to call the interpreter by executing a command
    command = 'python3 -m demucs.separate --dl -n demucs "{}"'.format(name)
    if(not os.getcwd() == os.path.join(os.environ.get("HOME"),"demucs_host_processor","demucs")):
        os.chdir("demucs")
    os.system(command)

    # paths to local files to upload
    results_paths = {
        'uid' : "{}".format(song_uid),
        'bass' : path.join(config.path_dir_results,"{}".format(song_uid),"bass.wav"),
        'drums' : path.join(config.path_dir_results,"{}".format(song_uid),"drums.wav"),
        'vocals' : path.join(config.path_dir_results,"{}".format(song_uid),"vocals.wav"),
        'other' : path.join(config.path_dir_results,"{}".format(song_uid),"other.wav")
    }

    # uploads tracks to cloud storage. When it's finished, it'll return de urls.
    # It's necessary to record the urls on the database, so the urls are sent to the API
    upload_songs(convert_wav_to_mp3(results_paths), userId, new_song_id)
    
    # freeing host
    pause.set()

def upload_songs(paths, user_id, song_id):
    # take result tracks and upload them to firebase cloud storage
    print(colored("[demucs_service]","blue"),"Finished separation. Uploading files to cloud storage")

    # start upload to google cloud
    bucket = cloud_storage_client.bucket('isolaatti-b6641.appspot.com')
    uid = paths.get("uid")
    #upload bass
    bass_blob_destination = "results/{}/{}/bass.mp3".format(user_id,uid)
    bass_blob = bucket.blob(bass_blob_destination)
    bass_blob.upload_from_filename(paths.get("mp3_bass"))
    bass_blob.make_public()
    result_bass_url = bass_blob.public_url

    #upload drums
    drums_blob_destination = "results/{}/{}/drums.mp3".format(user_id,uid)
    drums_blob = bucket.blob(drums_blob_destination)
    drums_blob.upload_from_filename(paths.get("mp3_drums"))
    drums_blob.make_public()
    result_drums_url = drums_blob.public_url

    #upload vocals
    vocals_blob_destination = "results/{}/{}/vocals.mp3".format(user_id,uid)
    vocals_blob = bucket.blob(vocals_blob_destination)
    vocals_blob.upload_from_filename(paths.get("mp3_vocals"))
    vocals_blob.make_public()
    result_vocals_url = vocals_blob.public_url

    #upload other
    other_blob_destination = "results/{}/{}/other.mp3".format(user_id,uid)
    other_blob = bucket.blob(other_blob_destination)
    other_blob.upload_from_filename(paths.get("mp3_other"))
    other_blob.make_public()
    result_other_url = other_blob.public_url

    # finally, urls are sent to API, and the user will be notified
    API.complete_record(song_id,result_bass_url,result_drums_url,result_vocals_url,result_other_url)
    

def record_to_database(google_storage_route,user_id):
    print("Sending request to WEB API")

def convert_wav_to_mp3(paths):

    song_uid = paths.get("uid")
    # command to be executed for each track to convert
    command_bass = "ffmpeg -i {} {}".format(paths.get("bass"),path.join(config.path_dir_results,"{}".format(song_uid),"bass.mp3"))
    command_drums = "ffmpeg -i {} {}".format(paths.get("drums"),path.join(config.path_dir_results,"{}".format(song_uid),"drums.mp3"))
    command_vocals = "ffmpeg -i {} {}".format(paths.get("vocals"),path.join(config.path_dir_results,"{}".format(song_uid),"vocals.mp3"))
    command_other = "ffmpeg -i {} {}".format(paths.get("other"),path.join(config.path_dir_results,"{}".format(song_uid),"other.mp3"))

    # executing four commands to convert
    os.system(command_bass)
    os.system(command_drums)
    os.system(command_other)
    os.system(command_vocals)

    return {
        'uid' : paths.get("uid"),
        'mp3_bass' : path.join(config.path_dir_results,"{}".format(song_uid),"bass.mp3"),
        'mp3_drums' : path.join(config.path_dir_results,"{}".format(song_uid),"drums.mp3"),
        'mp3_vocals' : path.join(config.path_dir_results,"{}".format(song_uid),"vocals.mp3"),
        'mp3_other' : path.join(config.path_dir_results,"{}".format(song_uid),"other.mp3")
    }



config.config()
print(colored("#### Demucs host processor ####","magenta",attrs=["bold"]))
print(colored("This host will be requesting a job every 10 seconds, until it finds one...","yellow",attrs=["bold"]))    

print("Setting up Google Firebase Admin")
# change path when configuring
#cred = credentials.Certificate("/home/erik/secrets/isolaatti-server/isolaatti-b6641-firebase-adminsdk-vwe7w-5263d66782.json")
#
#if not firebase_admin._apps:
 #   firebase_admin.initialize_app(cred, {
 #   'storageBucket' : 'isolaatti-b6641.appspot.com'
 #   })

cloud_storage_client = storage.Client()

# starts thread to be asking for a job in background
job_requester = Thread(target=request_job)
job_requester.start()