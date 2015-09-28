"""
Module with widgets specific to the blog.
"""
from datetime import datetime
from urllib.parse import urlparse

from gi.repository import Mx, GObject, Pango, Clutter, GtkClutter, WebKit, Gtk

import pisak
from pisak import logger, pager, widgets, utils, layout, unit, properties, \
    dirs
from pisak.blog import wordpress, config, html_parsers


_LOG = logger.get_logger(__name__)


"""
What should be displayed as a post tile title when there is no
post title defined.
"""
_NO_POST_TITLE = "BEZ TYTUŁU"


class PostTileSource(pager.DataSource):
    """
    Query the appropriate module for all posts that have been published on
    the blog. Produce a tile widget for each of them.
    """
    __gtype_name__ = "PisakBlogPostTileSource"

    __gproperties__ = {
        'blog-type': (
            str, '', '', '', GObject.PARAM_READWRITE)
    }

    def __init__(self):
        super().__init__()
        self._blog_type = None
        self.lazy_offset = 0

    @property
    def blog_type(self):
        return self._blog_type

    @blog_type.setter
    def blog_type(self, value):
        self._blog_type = value
        if value == 'own':
            now = datetime.now()
            self._data_sorting_key = lambda post: now - post.date
        elif value == 'followed':
            self._data_sorting_key = lambda post: post['date']

    def _produce_item(self, post_item):
        post = post_item.content
        tile = Tile()
        self._prepare_item(tile)
        frame = widgets.Frame()
        frame.set_style_class("PisakBlogPostTile")
        tile.add_child(frame)
        tile.connect("clicked", self.item_handler, post)
        tile.hilite_tool = widgets.Aperture()
        if isinstance(post, dict):
            post_title = post["title"]
            post_date = post["date"]
        else:
            post_title = post.title
            post_date = post.date
        tile.title.set_text(html_parsers.extract_text(post_title) or
                            _NO_POST_TITLE)
        if isinstance(post_date, str):
            post_date = datetime.strptime(
                post_date.split("+")[0].replace("T", " "),
                "%Y-%m-%d %H:%M:%S")
        tile.date.set_text(utils.date_to_when(post_date))
        return tile

    def _query_portion_of_data_by_number(self, offset, number):
        if self._blog_type == 'own':
            return wordpress.blog.get_many_posts(offset, number)
        elif self._blog_type == 'followed':
            return pisak.app.box['followed_blog'].get_many_posts(
                offset, number)

    def _check_ids_range(self):
        return list(map(str, range(0, 100)))


class BlogTileSource(pager.DataSource):
    """
    Produces tilea, each representing a single blog.
    """
    __gtype_name__ = "PisakBlogBlogTileSource"

    def __init__(self):
        super().__init__()
        self.data = config.get_followed_blogs()

    def _produce_item(self, blog):
        tile = widgets.PhotoTile()
        tile.style_class = "PisakBlogBlogTile"
        self._prepare_item(tile)
        frame = widgets.Frame()
        tile.add_child(frame)
        tile.hilite_tool = widgets.Aperture()
        url = urlparse(blog)
        blog_name = url.path[1:] if "blogi.pisak.org" in url.netloc \
            else url.netloc
        tile.label_text = blog_name
        tile.connect("clicked", self.item_handler, blog, blog_name)
        return tile


class Tile(widgets.PhotoTile):
    """
    Blog specific tile widget.
    """

    def __init__(self):
        super().__init__()
        margin = 8
        self.label = layout.Box()
        self.box.add_child(self.label)
        self.label.orientation = Clutter.Orientation.VERTICAL
        self.label.spacing = 20
        self.title = Mx.Label()
        self.date = Mx.Label()
        self.title.set_margin_right(margin)
        self.title.set_margin_left(margin)
        self.date.set_margin_right(margin)
        self.date.set_margin_left(margin)
        self.title.get_clutter_text().set_line_alignment(
                                Pango.Alignment.CENTER)
        self.date.get_clutter_text().set_line_alignment(
                                Pango.Alignment.CENTER)
        self.title.set_style_class("PisakBlogPostTileTitle")
        self.date.set_style_class("PisakBlogPostTileDate")
        self.label.add_child(self.title)
        self.label.add_child(self.date)


class UserPhoto(Mx.Image):
    """
    Photo of the blog author or user.
    """
    __gtype_name__ = "PisakBlogUserPhoto"

    def __init__(self):
        super().__init__()
        self.set_scale_mode(Mx.ImageScaleMode.FIT)
        try:
            self.set_from_file(wordpress.blog.USER_PHOTO_PATH)
        except GObject.GError as e:
            _LOG.warning(e)


class BlogPost(Clutter.ScrollActor, properties.PropertyAdapter):

    __gtype_name__ = "PisakBlogPost"
    __gproperties__ = {
        "ratio-height": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE),
        "ratio-width": (
            GObject.TYPE_FLOAT, None, None,
            0, 1., 0, GObject.PARAM_READWRITE)
    }
    
    def __init__(self):
        super().__init__()
        self.settings = WebKit.WebSettings()
        self.settings.set_property('auto-shrink-images', True)
        self.settings.set_property('default-font-family', 'Kelson Sans')
        self.settings.set_property('default-font-size', 30)
        self.view = WebKit.WebView()
        self.view.set_settings(self.settings)
        with open(dirs.get_blog_css_path()) as f:
            self.css = f.read()
        self.container = Gtk.ScrolledWindow()
        self.v_adj = self.container.get_vadjustment()
        self.container.add(self.view)
        self.view_actor = GtkClutter.Actor.new_with_contents(self.container)
        self.add_child(self.view_actor)
        self.view.connect("document-load-finished", self._reload)

    @property
    def ratio_width(self):
        return self._ratio_width

    @ratio_width.setter
    def ratio_width(self, value):
        self._ratio_width = value
        converted_value = unit.w(value)
        self.set_width(converted_value)
        self.view_actor.set_width(converted_value)

    @property
    def ratio_height(self):
        return self._ratio_height

    @ratio_height.setter
    def ratio_height(self, value):
        self._ratio_height = value
        converted_value = unit.h(value)
        self.set_height(converted_value)
        self.view_actor.set_height(converted_value)

    def load_html(self, html, ref_url="about::blank"):
        html = '<head><style>' + self.css + '</style></head><body>' + html + '</body>'
        self.view.load_string(html, "text/html", "utf-8", ref_url)

    def load_url(self, url):
        self.view.load_uri(url)

    def _reload(self, *args):
        self.view.set_visible(True)
        return False
