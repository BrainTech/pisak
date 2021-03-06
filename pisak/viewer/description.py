"""
Descriptor for PISAK photo viewer.
"""

from pisak import handlers
from pisak.viewer import model

from pisak.viewer import widgets  # @UnusedImport
import pisak.viewer.handlers  # @UnusedImport


def prepare_photo_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    album_id = data["album_id"]
    photo_id = data["photo_id"]

    data_source = script.get_object("photo_data_source")
    data_source.data_set_idx = album_id

    slideshow = script.get_object("slideshow_widget")
    slideshow.show_initial_photo_id(photo_id)

    handlers.button_to_view(window, script, "button_edition",
                    "viewer/photo_editing", (slideshow, album_id, photo_id))
    handlers.button_to_view(window, script, "button_album",
                            "viewer/album", {"album_id": album_id})
    handlers.button_to_view(window, script, "button_library", "viewer/main")

    library = model.get_library()
    header = script.get_object("header")
    header.set_text(library.get_category_by_id(album_id).name)


def prepare_album_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    album_id = data["album_id"]

    handlers.button_to_view(window, script, "button_library", "viewer/main")
    handlers.button_to_view(window, script, "button_start")

    library = model.get_library()
    header = script.get_object("header")
    header.set_text(library.get_category_by_id(album_id).name)

    data_source = script.get_object("library_data")

    def photo_tile_handler(tile, photo_id, album_id):
        window.load_view(
            "viewer/photo", {"photo_id": photo_id, "album_id": album_id})

    data_source.item_handler = photo_tile_handler
    data_source.data_set_idx = album_id
    data_source.emit('data-is-ready')


def prepare_library_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    library_data = script.get_object("library_data")
    library_data.item_handler = lambda tile, album: window.load_view(
        "viewer/album", {"album_id": album})
    handlers.button_to_view(window, script, "button_start")
    library_data.emit('data-is-ready')


def prepare_photo_editing_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    slideshow_widget, album_id, photo_id = data
    photo = script.get_object("slide")
    photo.photo_path = slideshow_widget.slide.photo_path
    photo.album_id = album_id

    handlers.button_to_view(window, script, "button_photo", "viewer/photo",
                        {"photo_id": photo_id, "album_id": album_id})
    handlers.button_to_view(window, script, "button_start")


viewer_app = {
    "app": "viewer",
    "type": "clutter",
    "views": [("photo", prepare_photo_view),
              ("album", prepare_album_view),
              ("main", prepare_library_view),
              ("photo_editing", prepare_photo_editing_view)]
}
