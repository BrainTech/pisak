
from time import time
import cv

from logger import get_logger
from utils import get_config

FPS_RESET = 3  # after how many seconds fps_counter is reseted/printed
LOGGER = get_logger('ImageProvider')

class ImageProvider(object):
    """Base class for all image providers, from different sources.

    After being started, it cyclically updates image, by calling _update_image
    method in intervals that it gets from databus, or if it's not there, from
    module defaults.
    It should be noted, that usually it's better to get images from
    ImagePreprocessor than directly from ImageProvider
    """
    config = get_config('image_provider', 1,
                      strict_resize=False)
    _instance = None
    _init_args = None
    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = cls(*args, **kwargs);
            cls._init_args = (args, kwargs)
        else:
            cls._instance._init_databus()
        if cls._init_args != (args, kwargs):
            LOGGER.warning("Init argumets are different!")
        return cls._instance

    def __init__(self, p_width=640, p_height=480, *args, **kwargs):
        self.size = (p_width, p_height)
        self.current_image = None
        self.get_time = time
        self.fps_print = False
        self.fps_counter = 0
        self.current_fps = 0
        self.fps_last_time = 0
        self.index = 0
        self.direction = 1
        self.resized_image = None
        self.mirrored = False
        self._strict_resize = self.config.strict_resize

    def current_frame_rate(self):
        diff = self.get_time() - self.fps_last_time
        if diff == 0:
            return 0
        return (self.fps_counter / diff)

    def _update_fps(self):
        self.fps_counter += 1
        cur_time = self.get_time()
        if (cur_time - self.fps_last_time >= FPS_RESET):
            if self.fps_print:
                print "Current frame rate is %.2f fps" % self.current_frame_rate()
            self.fps_counter = 0
            self.fps_last_time = cur_time

    def print_fps(self, fps_print=True):
        self.fps_print = fps_print

    def __repr__(self):
        return "ImageProvider"

    def set_image_data(self):
        self._update_image()
        img = self.current_image
        self.image_data = self.size, img.depth, img.nChannels, self.current_time
        self.index = 0

    def _update_image(self):
        """Updates current image
        Must be implemented in subclass.
        """

        if self.current_image is None:
            self.current_image = cv.LoadImage('resources\\camera_disconnected.png')  # cv.CreateImage(self.size, 8, 3)
        return cv.CloneImage(self.current_image)

    def update_image(self):
        """
        Returns an image and frame time.
        """
        self.current_time = self.get_time()
        l_image = self._update_image()
        if self.mirrored:
            cv.Flip(l_image, l_image, 1)
        if (self._strict_resize and l_image is not None
           and cv.GetSize(l_image) != self.size):
            if self.resized_image is None:
                self.resized_image = cv.CreateImage(self.size, l_image.depth,
                                                  l_image.nChannels)
            cv.Resize(l_image, self.resized_image)
            l_image = self.resized_image
        self._update_fps()
        self.current_image = l_image

        return l_image, self.current_time

    def getNext(self):
        self.update_image()
        return self.current_image, self.current_time

    def next(self):
        self.update_image()
        return self.current_image

    def set_time_function(self, func):
        self.get_time = func
        self.fps_last_time = func()
        self.fps_counter = 0

    def start(self):
        pass

    def stop(self):
        pass
    def clear(self):
        self.stop()
    def __del__(self):
        self.stop()
        self.clear()

    def get_type(self):
        return ImageProviderType.NONE

class ImageProviderType:
    NONE = 0
    CAMERA = 1
    MOVIE = 2
