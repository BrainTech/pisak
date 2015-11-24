"""
Module with operations on image data.
"""
import random
import os

from PIL import Image, ImageFilter
from gi.repository import Cogl, Clutter, GObject

from pisak import properties, configurator, logger


_LOG = logger.get_logger(__name__)


class ImageBuffer(Clutter.Actor, properties.PropertyAdapter,
                  configurator.Configurable):
    """
    Buffer containing a currently edited photo.
    """
    __gtype_name__ = "PisakImageBuffer"
    __gproperties__ = {
        "path": (
            GObject.TYPE_STRING,
            "path to photo",
            "path to photo slide",
            "noop",
            GObject.PARAM_READWRITE),
        "slide": (
            Clutter.Actor.__gtype__,
            "", "", GObject.PARAM_READWRITE)
    }

    PIXEL_FORMATS = {'1_1': Cogl.PixelFormat.G_8, 'L_1': Cogl.PixelFormat.A_8,
                     'RGB_2': Cogl.PixelFormat.RGB_565, 'RGB_3': Cogl.PixelFormat.RGB_888,
                     'RGBA_2': Cogl.PixelFormat.RGBA_4444, 'RGBA_4': Cogl.PixelFormat.RGBA_8888}

    SAVE_FORMATS = ['JPEG', 'PNG', 'TIFF', 'BMP']

    SAVE_DEFAULT_EXT = 'JPEG'

    SAVE_CONCATENATED_STRING = '_edited'

    def __init__(self):
        self._save_path = None
        self._save_format = None
        self.buffer = None
        self.original_photo = None
        self.zoom_timer = None
        self.noise_timer = None
        self.apply_props()

    def _create_save_path(self, original_path):
        directory, basename = os.path.split(original_path)
        name, ext = os.path.splitext(basename)
        name += self.SAVE_CONCATENATED_STRING
        self._save_path = os.path.join(directory, name + ext)
        if ext:
            proper_ext = ext[1:].upper()
            if proper_ext in self.SAVE_FORMATS:
                ext = proper_ext
            else:
                ext = self.SAVE_DEFAULT_EXT
        else:
            ext = self.SAVE_DEFAULT_EXT
        self._save_format = ext

    @property
    def path(self):
        """
        Path to the photo.
        """
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        if value is not None:
            self._create_save_path(value)
            try:
                self.original_photo = Image.open(self.path)
            except OSError:
                self.original_photo = Image.new("RGB", (100, 100))
            if self.original_photo.mode == 'P':
                self.original_photo = self.original_photo.convert()  # translates through built-in palette
            self.buffer = self.original_photo.copy()

    @property
    def slide(self):
        """
        Widget displaying the image.
        """
        return self._slide

    @slide.setter
    def slide(self, value):
        self._slide = value

    def mirror(self, *args):
        """
        Make a mirror reflection of the image along the horizontal axis.
        """
        self.buffer = self.buffer.transpose(Image.FLIP_LEFT_RIGHT)
        self._load()

    def grayscale(self, *args):
        """
        Apply grayscale filter to the image.

        :param args: some args.
        """
        self.buffer = self.buffer.convert('L')
        self._load()

    def rotate(self, *args):
        """
        Rotate the image by 90 degs clockwise.

        :param args: some args.
        """
        self.buffer = self.buffer.transpose(Image.ROTATE_90)
        self._load()

    def solarize(self, *args):
        """
        Solarize the image making it extra bright.

        :param args: some args.
        """
        threshold = 80
        bands = self.buffer.getbands()
        source = self.buffer.split()
        for idx in range(len(source)):
            if bands[idx] != 'A':
                out = source[idx].point(lambda i: i > threshold and 255-i)
                mask = source[idx].point(lambda i: i > threshold and 255)
                source[idx].paste(out, None, mask)
        mode = self.buffer.mode
        self.buffer = Image.merge(mode, source)
        self._load()

    def invert(self, *args):
        """
        Invert colors of the image.

        :param args: some args.
        """
        bands = self.buffer.getbands()
        source = self.buffer.split()
        for idx in range(len(source)):
            if bands[idx] != 'A':
                out = source[idx].point(lambda i: 255-i)
                source[idx].paste(out, None)
        mode = self.buffer.mode
        self.buffer = Image.merge(mode, source)
        self._load()

    def sepia(self, *args):
        """
        Apply sepia filter to the image.

        :param args: some args.
        """
        level = 50
        grayscale = self.buffer.convert('L')
        red = grayscale.point(lambda i: i + level*1.5)
        green = grayscale.point(lambda i: i + level)
        blue = grayscale.point(lambda i: i - level*0.5)
        bands = self.buffer.getbands()
        if 'A' not in bands:
            self.buffer = Image.merge('RGB', (red, green, blue))
        else:
            source = self.buffer.split()
            alpha = source[bands.index('A')]
            self.buffer = Image.merge('RGBA', (red, green, blue, alpha))
        self._load()

    def edges(self, *args):
        """
        Apply edges filter to the image.

        :param args: some args.
        """
        bands = self.buffer.getbands()
        source = self.buffer.split()
        for idx in range(len(source)):
            if bands[idx] != 'A':
                out = source[idx].filter(ImageFilter.FIND_EDGES)
                source[idx].paste(out, None)
        mode = self.buffer.mode
        self.buffer = Image.merge(mode, source)
        self._load()

    def contour(self, *args):
        """
        Apply contour filter to the image.

        :param args: some args.
        """
        bands = self.buffer.getbands()
        source = self.buffer.split()
        for idx in range(len(source)):
            if bands[idx] != 'A':
                out = source[idx].filter(ImageFilter.CONTOUR)
                source[idx].paste(out, None)
        mode = self.buffer.mode
        self.buffer = Image.merge(mode, source)
        self._load()

    def noise(self, *args):
        """
        Apply some random noise to the color bands of the image.
        This is performed as an animation.

        :param args: some args.
        """
        if not self.noise_timer:
            self.noise_timer = Clutter.Timeline.new(200)
            self.noise_timer.set_repeat_count(50)
            self.noise_timer.connect('completed', self._noise_update)
            self.noise_timer.connect('stopped', self._noise_finish)
            self.noise_timer.start()
        else:
            self.noise_timer.stop()

    def _noise_finish(self, *args):
        self.noise_timer = None

    def _noise_update(self, *args):
        level = 40
        bands = self.buffer.getbands()
        source = self.buffer.split()
        for idx in range(len(source)):
            if bands[idx] != 'A':
                out = source[idx].point(lambda i: i + random.uniform(-level, level))
                source[idx].paste(out, None)
        mode = self.buffer.mode
        self.buffer = Image.merge(mode, source)
        self._load()

    def zoom(self, *args):
        """
        Zoom the image. Zoom is performed as an animation.

        :param args: some args.
        """
        if not self.zoom_timer:
            self.zoom_timer = Clutter.Timeline.new(200)
            self.zoom_timer.set_repeat_count(35)
            self.zoom_timer.connect('completed', self._zoom_update)
            self.zoom_timer.connect('stopped', self._zoom_finish)
            self.zoom_timer.start()
        else:
            self.zoom_timer.stop()

    def _zoom_finish(self, *args):
        self.zoom_timer = None

    def _zoom_update(self, *args):
        width, height = self.buffer.size[0], self.buffer.size[1]
        x0, y0 = width/50, height/50
        x1, y1 = width-x0, height-y0
        self.buffer = self.buffer.transform((width, height), Image.EXTENT, (x0, y0, x1, y1))
        self._load()

    def original(self, *args):
        """
        Restore the original image.

        :param args: some args.
        """
        self.buffer = self.original_photo.copy()
        self._load()

    def save(self):
        """
        Save the currently edited buffer to a file.
        """
        err_msg = None
        if self._save_path and self._save_format:
            try:
                self.buffer.save(self._save_path, format=self._save_format)
            except Exception as exc:
                err_msg = exc
        else:
            err_msg = 'No save path for the currently edited photo.'
        if err_msg:
            LOG.error(err_msg)

    def _load(self):
        data = self.buffer.tobytes()
        width, height = self.buffer.size[0], self.buffer.size[1]
        pixel_count = width*height
        byte_count = len(data)
        byte_per_pixel = int(byte_count/pixel_count)
        row_stride = byte_count/height
        mode = self.buffer.mode
        pixel_format = '_'.join([mode, str(byte_per_pixel)])
        if pixel_format not in self.PIXEL_FORMATS:
            print('Pixel format {} not supported.'.format(pixel_format))
        else:
            cogl_pixel_format = self.PIXEL_FORMATS[pixel_format]
        self.slide.set_from_data(data, cogl_pixel_format, width, height, row_stride)
