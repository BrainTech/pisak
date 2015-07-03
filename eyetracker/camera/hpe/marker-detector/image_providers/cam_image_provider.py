from time import time

import cv
from cv import (CaptureFromCAM as capture_from_cam,
                SetCaptureProperty as set_capture_property,
                QueryFrame as query_frame)

from .image_provider import ImageProvider
from image_providers.image_provider import ImageProviderType

class CamImageProviderError(Exception):
    pass

class NoCameraConnectedError(CamImageProviderError):
    pass

class CamImageProvider(ImageProvider):
    """Provides image from camera connected to computer."""
    
    def __init__(self, p_camera_index=0, *args, **kwargs):
        if p_camera_index > 100:
            kwargs['p_width'] = p_camera_index
            kwargs['p_height'] = args[0]
            p_camera_index = -1
        super(CamImageProvider, self).__init__(*args, **kwargs)
        self.camera_index = p_camera_index
        self.capture = None
        self.start()

    def _update_image(self):
        l_timestamp = self.current_time
        if l_timestamp - self.last_timestamp > 0.5:
            l_last_string = self.current_image.tostring()
            l_frame = self.query_frame()            
            l_frame_string = l_frame.tostring()
            if l_frame_string == l_last_string:
                self.stop()
                raise NoCameraConnectedError('Camera disconnected')
        else:
            l_frame = self.query_frame()            
            self.last_timestamp = l_timestamp
        return l_frame
    
    def get_capture(self):
        return capture_from_cam(self.camera_index)
    
    def query_frame(self):
        return query_frame(self.capture)
    
    def start(self):
        if self.capture:
            return
        self.capture = self.get_capture()
#        Some cameras do cropping instead of resizing 
#        set_capture_property(self.capture, 
#                             cv.CV_CAP_PROP_FRAME_WIDTH, self.size[WIDTH])
#        set_capture_property(self.capture, 
#                             cv.CV_CAP_PROP_FRAME_HEIGHT, self.size[HEIGHT])

        tries = 30
        self.last_timestamp = time()
        while self.current_image is None and tries > 0:
            self.update_image()
            tries -= 1
        if tries == 0:
            raise NoCameraConnectedError('Camera not connected or not working properly')

    def stop(self):
        self.capture = None
        super(CamImageProvider, self).stop()

    
    def __repr__(self):        
        return "Cam nr %d" % self.camera_index
    
    def __del__(self):
        self.stop()
        ImageProvider.__del__(self)
    
    def get_type(self):
        return ImageProviderType.CAMERA

class CamImageProvider2(CamImageProvider):
    def get_capture(self):
        import cv2
        return cv2.VideoCapture(self.camera_index)
    def query_frame(self):
        import cv2
        cv2.waitKey()
        flag, img = self.capture.read()
        return img

if __name__ == '__main__':
    from image_providers import MovieImageProvider
    ip = CamImageProvider(0, 'test.avi')
    start = time()
    while time() < start + 5 and cv.WaitKey(1) != 27:
        img = ip.next()
        cv.ShowImage("image", img)
    ip.stop()
    del ip
    ip = MovieImageProvider('test.avi')
    img = ip.next()
    while img is not None and cv.WaitKey(1) != 27:
        cv.ShowImage('image2', img)
        img = ip.next()
    import os
    os.remove('test.avi')
