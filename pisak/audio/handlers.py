from pisak import signals
from pisak.audio import database_manager


@signals.registered_handler("audio/add_or_remove_from_favs")
def add_or_remove_from_favs(playback):
    """
    Add or remove the current audio stream object from the favourites.

    :param playback: media playback with audio to be marked as favourite
    """
    path = playback.filename
    if database_manager.is_track_in_favourites(path):
        database_manager.remove_track_from_favourites(path) 
    else:
       database_manager.add_track_to_favourites(path)
    
