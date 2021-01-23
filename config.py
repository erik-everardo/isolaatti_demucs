from os import path, mkdir, environ
# urls to make requests

url_get_job = "https://isolaattiapi.azurewebsites.net/api/GetJobFromQueue"
url_reserve_job = "https://isolaattiapi.azurewebsites.net/api/ReserveSongFromQueue"
url_started_process = "https://isolaattiapi.azurewebsites.net/api/StartedProcess"
url_completed_process = "https://isolaattiapi.azurewebsites.net/api/CompleteSongRecord"
url_create_song_record = "https://isolaattiapi.azurewebsites.net/api/CreateSongRecord"

# paths
path_dir_dw_songs = path.join(environ.get("HOME"),"downloaded_songs_isolaatti")
path_dir_results = path.join(environ.get("HOME"),"isolaatti_demucs","demucs","separated","light_extra")

url_google_bucket = "https://isolaatti-b6641.appspot.com.storage.googleapis.com/"

# type here settings to do everytime the server starts
def config():
    if(not path.isdir(path_dir_dw_songs)):
        mkdir(path_dir_dw_songs)
        print(path_dir_dw_songs + " directory was created!")
