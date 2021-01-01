# Erik, last modified november 2020
# Isolaatti Project
# centralized code for WEB API calls
import config
import requests

def started_process(song_id):
    query = {
        'songId' : song_id
    }
    requests.post(config.url_started_process,query)

def create_song_record(user_id,song_name,song_artist):
    query = {
        'userId' : user_id,
        'fileName' : song_name,
        'songArtist' : song_artist
    }
    return requests.post(config.url_create_song_record,query)

def complete_record(song_id, bass_url, drums_url, vocals_url, other_url, uid):
    query = {
        'songId'   : song_id,
        'bassUrl'  : bass_url,
        'drumsUrl' : drums_url,
        'voiceUrl' : vocals_url,
        'otherUrl' : other_url,
        'uid'      : uid
    }
    requests.post(config.url_completed_process, query)

def get_job_from_queue():
    return requests.get(config.url_get_job)

def reserve_job_from_queue(queue_element_id):
    query = {
        'elementId' : queue_element_id
    }
    requests.post(config.url_reserve_job,query)