"""
Widgets for the viewer application.
"""
import os.path

from gi.repository import Mx, GObject, Clutter
import cairo

import pisak
from pisak import res, widgets, layout, pager, properties, unit, configurator
from pisak.viewer import image, model


class SlideShow(layout.Bin, configurator.Configurable):
    """
    Widget for displaying and managing one photo and for running
    and managing slideshow that can be displayed
    either on fullscreen or in the standard view.
    """
    __gtype_name__ = "PisakViewerSlideShow"
    __gsignals__ = {
        "progressed": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_FLOAT, GObject.TYPE_INT64)),
        "limit-declared": (
            GObject.SIGNAL_RUN_FIRST, None,
            (GObject.TYPE_INT64,))
    }
    __gproperties__ = {
        "data-source": (
            pager.DataSource.__gtype__, "", "", GObject.PARAM_READWRITE),
        "transition-duration": (
            GObject.TYPE_INT64, "transition duration",
            "duration of slides transition", 0,
            GObject.G_MAXUINT, 1000, GObject.PARAM_READWRITE),
        "idle-duration": (
            GObject.TYPE_INT64, "idle duration",
            "duration of one slide exposition", 0,
            GObject.G_MAXUINT, 5000, GObject.PARAM_READWRITE),
        "slideshow-on-fullscreen": (
            GObject.TYPE_BOOLEAN, "if fullscreen",
            "if slideshow on fullscreen", False,
            GObject.PARAM_READWRITE),
         "exit-button": (
            Clutter.Actor.__gtype__,
            "", "", GObject.PARAM_READWRITE)
    }

    def __init__(self):
        self.index = 0
        self.new_slide_transition = Clutter.PropertyTransition.new("x")
        self.new_slide_transition.connect("stopped", self._clean_up)
        self.old_slide_transition = Clutter.PropertyTransition.new("x")
        self.set_clip_to_allocation(True)
        self.transition_duration = 1000
        self.idle_duration = 1000
        self.pending_slides = ()
        self.slideshow_on = False
        self.fullscreen_on = False
        self.slideshow_on_fullscreen = True
        self.old_slide = None
        self.slide = None
        self.album_length = None
        self.cached_slide_width = None
        self.cached_slide_height = None

        self._prev_content = None
        self._middleware = None
        self._exit_button = None

        self._cover = Clutter.Actor()
        self._cover.set_layout_manager(Clutter.BinLayout())
        self._cover.set_size(unit.w(1), unit.h(1))

        self.apply_props()

    @property
    def exit_button(self):
        """
        Widget that can be used to exit the fullscreen mode slideshow.
        """
        return self._exit_button

    @exit_button.setter
    def exit_button(self, value):
        self._exit_button = value
        self._cover.add_child(value)

    @property
    def data_source(self):
        """
        Viewer data source.
        """
        return self._data_source

    @data_source.setter
    def data_source(self, value):
        self._data_source = value

    @property
    def transition_duration(self):
        """
        Duration of transition between photos.
        """
        return self.new_slide_transition.get_duration()

    @transition_duration.setter
    def transition_duration(self, value):
        self.new_slide_transition.set_duration(value)
        self.old_slide_transition.set_duration(value)

    @property
    def idle_duration(self):
        """
        Duration of one photo display in a slideshow mode.
        """
        return self._idle_duration

    @idle_duration.setter
    def idle_duration(self, value):
        self._idle_duration = value

    @property
    def slideshow_on_fullscreen(self):
        """
        Whether slideshow should be displayed in the fullscreen mode, boolean.
        """
        return self._slideshow_on_fullscreen

    @slideshow_on_fullscreen.setter
    def slideshow_on_fullscreen(self, value):
        self._slideshow_on_fullscreen = value

    def show_initial_photo_id(self, photo_id):
        """
        Display some arbitrary photo.

        :param photo_index: index of the photo to be shown.
        """
        library = model.get_library()
        photo = library.get_item_by_id(photo_id)
        index = self.data_source.data.index(photo)
        self.show_initial_slide(index)

    def show_initial_slide(self, initial_index=0):
        """
        Show the first slide from the whole set of slides.

        :param initial_index: index of the slide to be shown.
        """
        self.album_length = len(self.data_source.data)
        self.emit("limit-declared", self.album_length)
        self.index = initial_index
        if self.data_source is not None:
            self.pending_slides = self.data_source.get_pending_slides(
                self.index)
            self.slide = self.data_source.get_slide(self.index)
            self.add_child(self.slide)
        self.emit("progressed",
                  float(self.index+1) / self.album_length,
                  self.index+1)

    def slideshow_timeout(self):
        """
        Function called on a slideshow timeout.

        :return: True or False, depending on the
        state of the slideshow, set externally.
        """
        if self.slideshow_on:
            self.next_slide()
            return True
        else:
            return False

    def next_slide(self):
        """
        Display the photo slide following the currently displayed one.
        """
        if self.old_slide is None and self.album_length > 1:
            self.index = (self.index + 1) % self.album_length
            self.old_slide = self.slide
            self.slide = self.pending_slides[1]
            self.slide.set_x(unit.size_pix[0])
            if self.fullscreen_on:
                self.cover_frame.add_child(self.slide)
                self.slide.set_size(unit.size_pix[0], unit.size_pix[1])
            else:
                self.add_child(self.slide)
            self.pending_slides = self.data_source.get_pending_slides(
                self.index)
            self.new_slide_transition.set_from(unit.size_pix[0])
            self.new_slide_transition.set_to(0)
            self.old_slide_transition.set_to(-1*unit.size_pix[0])
            self.old_slide.add_transition("x", self.old_slide_transition)
            self.slide.add_transition("x", self.new_slide_transition)
            self.emit("progressed",
                      float(self.index+1) / self.album_length,
                      self.index+1)

    def previous_slide(self):
        """
        Display the photo slide previous to the currently displayed one.
        """
        if self.old_slide is None and self.album_length > 1:
            self.index = self.index - 1 if self.index > 0 \
                else self.album_length - 1
            self.old_slide = self.slide
            self.slide = self.pending_slides[0]
            self.slide.set_x(-1*unit.size_pix[0])
            if self.fullscreen_on:
                self.cover_frame.add_child(self.slide)
                self.slide.set_size(unit.size_pix[0], unit.size_pix[1])
            else:
                self.add_child(self.slide)
            self.pending_slides = self.data_source.get_pending_slides(
                self.index)
            self.new_slide_transition.set_from(-1*unit.size_pix[0])
            self.new_slide_transition.set_to(0)
            self.old_slide_transition.set_to(unit.size_pix[0])
            self.old_slide.add_transition("x", self.old_slide_transition)
            self.slide.add_transition("x", self.new_slide_transition)
            self.emit("progressed",
                      float(self.index+1) / self.album_length,
                      self.index+1)

    def run(self):
        """
        Run automatic slideshow. Turn on the fullscreen mode if the
        corresponding property is setted to True.
        """
        if self.slideshow_on_fullscreen:
            self.fullscreen_on = True
            self.stage = self.get_stage()
            self.cover_frame = Clutter.Actor()
            self.cover_frame.set_size(unit.size_pix[0], unit.size_pix[1])
            self.slide.remove_transition("x")
            self.remove_child(self.slide)
            self.cover_frame.add_child(self.slide)
            self.slide.set_x(0)
            cover_frame_color = Clutter.Color.new(0, 0, 0, 255)
            self.cover_frame.set_background_color(cover_frame_color)
            if (self.cached_slide_width is None and
                    self.cached_slide_height is None):
                self.cached_slide_width, self.cached_slide_height = \
                    self.slide.get_size()
            self.slide.set_size(unit.size_pix[0], unit.size_pix[1])
            self.stage.add_child(self.cover_frame)

            self._middleware = pisak.app.window.input_group.middleware
            if self._middleware in (None, "sprite"):
                self.stage.add_child(self._cover)
                if self._middleware == "sprite":
                    self._prev_content = pisak.app.window.input_group.content
                    pisak.app.window.input_group.stop_middleware()
                    pisak.app.window.input_group.load_content(self._cover)

        self.slideshow_on = True
        Clutter.threads_add_timeout(0, self.idle_duration,
                                        lambda _: self.slideshow_timeout(),
                                        None)

    def stop(self):
        """
        Stop the currently running, automatic slideshow.
        If in fullscreen mode- exit fullscreen mode.
        """
        self.slideshow_on = False
        if self.slideshow_on_fullscreen:
            self.slide.remove_transition("x")
            self.cover_frame.remove_child(self.slide)
            self.stage.remove_child(self.cover_frame)
            self.slide.set_size(self.cached_slide_width,
                                self.cached_slide_height)
            self.slide.set_x(0)
            self.add_child(self.slide)

            if self._middleware in (None, "sprite"):
                self.stage.remove_child(self._cover)
                if self._middleware == "sprite":
                    pisak.app.window.input_group.stop_middleware()
                    pisak.app.window.input_group.load_content(self._prev_content)

            self.fullscreen_on = False

    def _clean_up(self, source, event):
        """
        Func used as a signal handler. Clean up after stoppage of the
        new photo slide 'x' transition. Remove transitions and
        free the old slide.
        """
        self.slide.remove_transition("x")
        self.old_slide.remove_transition("x")
        if self.old_slide is not None:
            if self.contains(self.old_slide):
                self.remove_child(self.old_slide)
            elif self.slideshow_on_fullscreen:
                if self.cover_frame.contains(self.old_slide):
                    self.cover_frame.remove_child(self.old_slide)
        if (self.cached_slide_width is not None and
                self.cached_slide_width is not None):
            self.old_slide.set_size(self.cached_slide_width,
                                    self.cached_slide_height)
        self.old_slide = None


class PhotoSlidesSource(pager.DataSource):
    """
    Communicate with the library manager and dynamically
    generate PhotoSlides, each for one photo from the specified album.
    """
    __gtype_name__ = "PisakViewerPhotoSlidesSource"

    def __init__(self):
        super().__init__()
        self.item_ratio_height = 0.7
        self.item_ratio_width = 0.68
        self.library = model.get_library()
        self.data_generator = lambda value: \
                        self.library.get_category_by_id(value).get_all_items()
        self.data_sets_count = len(self.library.get_all_categories())

    def get_pending_slides(self, index):
        """
        Return the list consisting of two photo slide instances.
        One corresponding to the data item prior to the given index
        and one to the following item.
        :param index: index pointing to the data list between the
        indexes of demanding slides
        """
        return (self._generate_slide(index-1),
                self._generate_slide((index+1)%len(self.data)),)
            
    def get_slide(self, index):
        """
        Return photo slide instance corresponding to the
        data item at the given index.
        """
        return self._generate_slide(index)

    def get_slide_backward(self, index):
        """
        Return photo slide instance corresponding to the
        data item prior to the one at given index.
        """
        return self._generate_slide(index-1)
        
    def get_slide_forward(self, index):
        """
        Return photo slide instance corresponding to the
        data item following the one at the given index.
        """
        return self._generate_slide((index+1)%len(self.data))

    def _generate_slide(self, index):
        slide = PhotoSlide()
        slide.ratio_height = self.item_ratio_height
        slide.ratio_width = self.item_ratio_width
        slide.photo_path = self.data[index].path
        return slide


class LibraryTilesSource(pager.DataSource):
    """
    Communicate with the library manager and dynamically generates the
    required number of PhotoTiles, each representing one album from
    the library.
    """
    __gtype_name__ = "PisakViewerLibraryTilesSource"

    def __init__(self):
        super().__init__()
        self.data = list(model.get_library().get_all_categories())

    def _produce_item(self, album):
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        tile.label_text = album.name
        tile.style_class = "PisakViewerPhotoTile"
        tile.connect("clicked", self.item_handler, album.id)
        tile.hilite_tool = widgets.Aperture()
        preview_path = album.get_preview_path()
        if preview_path:
            tile.preview_path = preview_path
        return tile


class AlbumTilesSource(pager.DataSource):
    """
    Communicate with the library manager and dynamically
    generate the required number of PhotoTiles, each representing
    one photo from the specified album.
    """
    __gtype_name__ = "PisakViewerAlbumTilesSource"

    def __init__(self):
        super().__init__()
        self.library = model.get_library()
        self.data_generator = lambda value: \
                        self.library.get_category_by_id(value).get_all_items()
        self.data_sets_count = len(self.library.get_all_categories())

    def _produce_item(self, data_item):
        tile = widgets.PhotoTile()
        self._prepare_item(tile)
        tile.hilite_tool = widgets.Aperture()
        tile.connect("clicked", self.item_handler,
                        data_item.id, self.data_set_idx)
        tile.scale_mode = Mx.ImageScaleMode.FIT
        tile.preview_path = data_item.path
        return tile


class PhotoSlide(layout.Bin, configurator.Configurable):
    """
    Display a single image fitted within the given allocation.
    """
    __gtype_name__ = "PisakViewerPhotoSlide"
    __gproperties__ = {
        "photo_path": (
            GObject.TYPE_STRING,
            "path to photo",
            "path to photo slide",
            "noop",
            GObject.PARAM_READWRITE),
        "transition_duration": (
            GObject.TYPE_INT64, "transition duration",
            "duration of photo transition", 0,
            GObject.G_MAXUINT, 500, GObject.PARAM_READWRITE),
        "image_buffer": (
            image.ImageBuffer.__gtype__,
            "", "", GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self.photo_path = None
        self.image_buffer = None
        self.photo = Mx.Image()
        self.photo.set_scale_mode(Mx.ImageScaleMode.FIT)
        self.add_child(self.photo)
        self.apply_props()

    @property
    def image_buffer(self):
        """
        Buffer storing the image.
        """
        return self._image_buffer

    @image_buffer.setter
    def image_buffer(self, value):
        self._image_buffer = value
        if self.photo_path is not None:
            value.path = self.photo_path
            value.slide = self

    @property
    def photo_path(self):
        """
        Path to the photo.
        """
        return self._photo_path

    @photo_path.setter
    def photo_path(self, value):
        self._photo_path = value
        if value is not None:
            try:
                self.photo.set_from_file_at_size(value, unit.size_pix[0],
                                             unit.size_pix[1])
            except GObject.GError:
                self.photo.clear()
            if self.image_buffer is not None:
                self.image_buffer.slide = self
                self.image_buffer.path = value

    @property
    def transition_duration(self):
        """
        Duration of an animation displayed
        when showing the photo.
        """
        return self.photo.get_transition_duration()

    @transition_duration.setter
    def transition_duration(self, value):
        self.photo.set_transition_duration(value)

    def set_from_data(self, data, mode, width, height, row_stride):
        self.photo.set_from_data(data, mode, width, height, row_stride)
