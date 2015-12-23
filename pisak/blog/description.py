"""
Module with specific description for blog application.
"""
import socket
import time

from gi.repository import Clutter

from pisak import handlers
from pisak.blog import widgets, wordpress, config, html_parsers, rest_client

from pisak.viewer import model as viewer_model

import pisak.layout  # @UnusedImport
import pisak.speller.widgets  # @UnusedImport
import pisak.speller.handlers  # @UnusedImport
import pisak.viewer.widgets  # @UnusedImport
import pisak.viewer.handlers  # @UnusedImport
import pisak.blog.widgets  # @UnusedImport
import pisak.blog.handlers  # @UnusedImport


MESSAGES = {
    'too-slow-connection': 'Błąd połączenia - \nzbyt wolne połączenie z internetem.'
}


def prepare_main_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    title_text = "   _   BLOG"
    wordpress.blog.pending_post = None
    handlers.button_to_view(window, script, "button_others", "blog/followed_blogs")
    handlers.button_to_view(window, script, "button_my_blog", "blog/all_posts")
    handlers.button_to_view(window, script, "button_exit")
    title = config.get_blog_config()["title"]
    blog_title = script.get_object("title")
    blog_title.set_text(title + title_text)


def prepare_about_me_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    try:
        about = wordpress.blog.get_about_me_page()
    except socket.timeout:
        window.load_popup(MESSAGES['too-slow-connection'], 'main_panel/main')
    else:
        about_info = script.get_object("about")
        plain = html_parsers.extract_text(about.content)
        if plain:
            about_info.set_text(plain)

        handlers.button_to_view(window, script, "button_edit_desc",
                                "blog/speller_about_me")
        handlers.button_to_view(window, script, "button_edit_photo",
                                "blog/viewer_about_me_library")
        handlers.button_to_view(window, script, "button_exit")
        handlers.button_to_view(window, script, "button_back", "blog/main")


def prepare_all_posts_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    wordpress.blog.pending_post = None
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_about", "blog/about_me")
    handlers.button_to_view(window, script, "button_back", "blog/main")
    handlers.button_to_view(
        window, script, "button_new_post", "blog/speller_post")
    posts_data = script.get_object("posts_data")

    def load_view(tile, post):
        posts_data.clean_up()
        window.load_view("blog/single_post",
                         {"post": post.content,
                          "posts": posts_data,
                          "post_item": post})

    posts_data.item_handler = load_view
    title = config.get_blog_config()["title"]
    blog_title = script.get_object("header")
    blog_title.set_text(title)
    date_widget = script.get_object("date")
    today = "DATA:   " + time.strftime("%d-%m-%Y")
    date_widget.set_text(today)
    posts_data.lazy_loading = True


def prepare_single_post_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """

    post = data["post"]
    post_item = data["post_item"]

    content_box = script.get_object("post_text")

    title = config.get_blog_config()["title"]
    blog_title = script.get_object("header")
    blog_title.set_text(title)

    def load_new_post(direction, arbitrary_post=None):
        if arbitrary_post:
            post_to_load = arbitrary_post
        else:
            nonlocal post_item

            posts = data["posts"].data
            index = posts.index(post_item)
            index += direction
            if index == len(posts):
                index = 0
            post_to_load = posts[index]

        content = post_to_load.content
        wordpress.blog.pending_post = content
        try:
            content_box.load_html(wordpress.blog.compose_post_view(content))
        except socket.timeout:
            window.load_popup(MESSAGES['too-slow-connection'], 'main_panel/main')

    load_new_post(0, post_item)

    data['previous_view'] = 'blog/single_post'

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_back", "blog/all_posts")
    handlers.button_to_view(window, script, "button_about", "blog/about_me")
    handlers.button_to_view(window, script, "button_delete_post",
                            "blog/all_posts")
    handlers.button_to_view(window, script, "button_post_edit",
                            "blog/speller_post")
    handlers.button_to_view(
        window, script, "button_comment", "blog/speller_comment", data)

    handlers.connect_button(script, "button_next_post", load_new_post, 1)
    handlers.connect_button(script, "button_previous_post", load_new_post,
                            -1)


def prepare_followed_blog_single_post_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    post = data["post"]
    post_item = data['post_item']
    content = script.get_object("post_text")

    blog_name = script.get_object("header")
    blog_name.set_text(data["blog_name"])

    def load_new_post(direction, arbitrary_post=None):
        if arbitrary_post:
            post_to_load = arbitrary_post
        else:
            nonlocal post_item

            posts = data['posts'].data
            index = posts.index(post_item)
            index += direction
            if index == len(posts):
                index = 0
            post_to_load = posts[index]
        try:
            content.load_html(data["blog"].compose_post_view(post_to_load.content))
        except socket.timeout:
            window.load_popup(MESSAGES['too-slow-connection'], 'main_panel/main')

    load_new_post(0, post_item)

    data['previous_view'] = 'blog/followed_blog_single_post'

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_back", "blog/followed_blog_all_posts", data)
    handlers.button_to_view(window, script, "button_about", "blog/about_me")
    handlers.button_to_view(
        window, script, "button_comment", "blog/speller_comment", data)

    handlers.connect_button(script, "button_next_post", load_new_post, 1)
    handlers.connect_button(script, "button_previous_post", load_new_post,
                            -1)


def prepare_followed_blog_all_posts_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_about", "blog/about_me")
    handlers.button_to_view(window, script, "button_back", "blog/followed_blogs")
    blog_url = data["blog_url"]
    blog_name = data["blog_name"]
    blog = rest_client.Blog(blog_url)
    app.box['followed_blog'] = blog
    posts_data = script.get_object("posts_data")

    def load_view(tile, post):
        posts_data.clean_up()
        window.load_view("blog/followed_blog_single_post",
                         {"blog": blog , "post": post.content,
                          "post_item": post,
                          "blog_name": blog_name,
                          "blog_url": blog_url,
                          "posts": posts_data})

    posts_data.item_handler = load_view
    blog_name_widget = script.get_object("header")
    blog_name_widget.set_text(blog_name)
    date_widget = script.get_object("date")
    today = "DATA:   " + time.strftime("%d-%m-%Y")
    date_widget.set_text(today)
    posts_data.lazy_loading = True


def prepare_followed_blogs_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_about", "blog/about_me")
    handlers.button_to_view(window, script, "button_back", "blog/main")
    blogs_data = script.get_object("blogs_data")
    blogs_data.item_handler = lambda tile, blog_url, blog_name: \
        window.load_view("blog/followed_blog_all_posts",
                        {"blog_url": blog_url, "blog_name": blog_name})


def prepare_speller_post_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    if wordpress.blog.pending_post is not None:
        text_field = script.get_object("text_box")
        plain_text = html_parsers.extract_text(
            wordpress.blog.pending_post.content)
        if plain_text:
            text_field.type_text(plain_text)
    else:
        wordpress.blog.prepare_empty_post()
    handlers.button_to_view(
        window, script, "button_proceed", "blog/speller_title")
    handlers.button_to_view(window, script, "button_exit")


def prepare_speller_title_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    text_field = script.get_object("text_box")
    post = wordpress.blog.pending_post
    if post.title and post.title != "Untitled":
        text_field.type_text(post.title)
    handlers.button_to_view(
        window, script, "button_proceed", "blog/viewer_library")
    handlers.button_to_view(window, script, "button_exit")


def prepare_viewer_library_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    library_data = script.get_object("library_data")
    library_data.item_handler = lambda tile, album: window.load_view(
        "blog/viewer_album", {"album_id": album})
    handlers.button_to_view(window, script, "button_start")
    handlers.button_to_view(
        window, script, "button_publish_blog", "blog/all_posts")


def prepare_viewer_album_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    library = viewer_model.get_library()

    def attach_photo(tile):
        wordpress.blog.post_images.append(tile.preview_path)

    handlers.button_to_view(
        window, script, "button_library", "blog/viewer_library")
    handlers.button_to_view(
        window, script, "button_publish_blog", "blog/all_posts")
    handlers.button_to_view(window, script, "button_start")
    album_id = data["album_id"]
    header = script.get_object("header")
    header.set_text(library.get_category_by_id(album_id).name)
    album_data = script.get_object("album_data")
    album_data.item_handler = lambda tile, photo_id, album_id: \
        attach_photo(tile)
    album_data.data_set_idx = album_id


def prepare_speller_about_me_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    try:
        bio = wordpress.blog.get_about_me_page()
    except socket.timeout:
        window.load_popup(MESSAGES['too-slow-connection'], 'main_panel/main')
    else:
        plain_bio = html_parsers.extract_text(bio.content)
        if plain_bio:
            text_widget = script.get_object("text_box")
            text_widget.type_text(plain_bio)
        handlers.button_to_view(window, script, "button_proceed", "blog/about_me")
        handlers.button_to_view(window, script, "button_exit")


def prepare_viewer_about_me_library_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    library_data = script.get_object("library_data")
    library_data.item_handler = lambda tile, album: window.load_view(
        "blog/viewer_about_me_album", {"album_id": album})
    handlers.button_to_view(window, script, "button_start")


def prepare_viewer_about_me_album_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    library = viewer_model.get_library()

    def pick_photo(tile):
        try:
            wordpress.blog.update_about_me_photo(tile.preview_path)
        except socket.timeout:
            window.load_popup(MESSAGES['too-slow-connection'], 'main_panel/main')
        else:
            window.load_view("blog/about_me")

    handlers.button_to_view(window, script, "button_library",
                            "blog/viewer_about_me_library")
    handlers.button_to_view(window, script, "button_start")
    album_id = data["album_id"]
    header = script.get_object("header")
    header.set_text(library.get_category_by_id(album_id).name)
    album_data = script.get_object("album_data")
    album_data.item_handler = lambda tile, photo_id, album_id: pick_photo(tile)
    album_data.data_set_idx = album_id


def prepare_speller_comment_view(app, window, script, data):
    """
    View preparator.

    :param app: reference to the application, :see: :module:`pisak.application`.
    :param window: application main window, :class:`pisak.window.Window` instance.
    :param script: ClutterScript with the view description.
    :param data: some specific data.
    """
    def publish_comment():
        text_widget = script.get_object("text_box")
        text = html_parsers.apply_linebreaks(text_widget.get_text())

        try:
            if data['previous_view'] == 'blog/single_post':
                own_blog = wordpress.blog
                own_blog.add_comment(data['post'].id, text)
            else:
                followed_blog = wordpress.Blog(data["blog_url"])
                followed_blog.add_comment(data["post"]["ID"], text)
        except socket.timeout:
            window.load_popup(MESSAGES['too-slow-connection'], 'main_panel/main')

    handlers.button_to_view(window, script, "button_exit")
    handlers.connect_button(script, "button_proceed", publish_comment)
    handlers.button_to_view(
         window, script, "button_proceed", data['previous_view'], data)


blog_app = {
    "app": "blog",
    "type": "gtk",
    "views": [
        ("main", prepare_main_view),
        ("about_me", prepare_about_me_view),
        ("all_posts", prepare_all_posts_view),
        ("single_post", prepare_single_post_view),
        ("followed_blogs", prepare_followed_blogs_view),
        ("speller_post", prepare_speller_post_view),
        ("speller_title", prepare_speller_title_view),
        ("viewer_library", prepare_viewer_library_view),
        ("viewer_album", prepare_viewer_album_view),
        ("speller_about_me", prepare_speller_about_me_view),
        ("viewer_about_me_library", prepare_viewer_about_me_library_view),
        ("viewer_about_me_album", prepare_viewer_about_me_album_view),
        ("followed_blog_single_post", prepare_followed_blog_single_post_view),
        ("followed_blog_all_posts", prepare_followed_blog_all_posts_view),
        ("speller_comment", prepare_speller_comment_view)
    ]
}
