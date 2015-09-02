from pisak import signals
from pisak.viewer import image, model


@signals.registered_handler("viewer/slideshow_toggle")
def slideshow_toggle(slideshow_widget):
    """
    Turn on or turn off the automatic slideshow.

    :param slideshow_widget: pisak slideshow instance
    """
    if slideshow_widget.slideshow_on is True:
        slideshow_widget.stop()
    else:
        slideshow_widget.run()


@signals.registered_handler("viewer/next_slide")
def next_slide(slideshow_widget):
    """
    Move to the next slide.

    :param slideshow_widget: pisak slideshow instance
    """
    slideshow_widget.next_slide()


@signals.registered_handler("viewer/previous_slide")
def previous_slide(slideshow_widget):
    """
    Move to the previous slide.

    :param slideshow_widget: pisak slideshow instance
    """
    slideshow_widget.previous_slide()


@signals.registered_handler("viewer/add_or_remove_from_favs")
def add_or_remove_from_favs(slideshow_widget):
    """
    Add or remove the currently displayed photo from the favourites.

    :param slideshow_widget: pisak slideshow instance
    """
    path = slideshow_widget.slide.photo_path
    lib = model.get_library()
    if lib.is_in_favourites(path):
        lib.remove_item_from_favourites(path)
    else:
        lib.add_item_to_favourites(path)


@signals.registered_handler("viewer/add_photo_to_favourites")
def add_photo_to_favourites(slideshow_widget):
    """
    Add the currently displayed photo to the favourites.

    :param slideshow_widget: pisak slideshow instance
    """
    path = slideshow_widget.slide.photo_path
    model.get_library().add_item_to_favourites(path)


@signals.registered_handler("viewer/remove_photo_from_favourites")
def remove_photo_from_favourites(slideshow_widget):
    """
    Remove the currently displayed photo from the favourites.

    :param slideshow_widget: pisak slideshow instance
    """
    path = slideshow_widget.slide.photo_path
    model.get_library().remove_item_from_favourites(path)
    

@signals.registered_handler("viewer/zoom")
def zoom(slide_space):
    """
    Zoom the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.zoom()


@signals.registered_handler("viewer/contour")
def contour(slide_space):
    """
    Apply a contour effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.contour()


@signals.registered_handler("viewer/edges")
def edges(slide_space):
    """
    Apply a edges effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.edges()


@signals.registered_handler("viewer/sepia")
def sepia(slide_space):
    """
    Apply a sepia effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.sepia()
        

@signals.registered_handler("viewer/invert")
def invert(slide_space):
    """
    Apply a color invert effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.invert()


@signals.registered_handler("viewer/rotate")
def rotate(slide_space):
    """
    Rotate the photo for 90 degrees.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.rotate()


@signals.registered_handler("viewer/mirror")
def mirror(slide_space):
    """
    Apply a mirror effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.mirror()


@signals.registered_handler("viewer/grayscale")
def grayscale(slide_space):
    """
    Apply a grayscale effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.grayscale()


@signals.registered_handler("viewer/noise")
def noise(slide_space):
    """
    Apply a noise effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.noise()


@signals.registered_handler("viewer/solarize")
def solarize(slide_space):
    """
    Apply a solarize effect to the photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
        slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.solarize()


@signals.registered_handler("viewer/original")
def original(slide_space):
    """
    Remove all the applied effects an operations and go back
    to the original photo.

    :param slide_space: container with the pisak slide instance inside
    """
    slide = slide_space.get_children()[0]
    if slide.image_buffer is None:
       slide.image_buffer = image.ImageBuffer()
    slide.image_buffer.original()
