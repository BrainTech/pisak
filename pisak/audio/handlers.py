from pisak import signals
from pisak.audio import db_manager


@signals.registered_handler("audio/add_or_remove_from_favs")
def add_or_remove_from_favs(playback):
    """
    Add or remove the current audio stream object from the favourites.

    :param playback: media playback with audio to be marked as favourite
    """
    path = playback.filename
    if db_manager.is_track_in_favourites(path):
        db_manager.remove_track_from_favourites(path)
    else:
       db_manager.add_track_to_favourites(path)
    
