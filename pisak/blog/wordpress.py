"""
Module with tools to interface a WordPress based blog.
"""
import time
import socket
import threading
import os.path
from io import BytesIO

import magic
import wordpress_xmlrpc
import requests
from PIL import Image

from pisak import logger, dirs
from pisak.blog import config, exceptions, html_parsers


_LOG = logger.get_logger(__name__)


blog = None


def initialize_session():
    """
    Initialize the blog instance and establish the connection for the
    on-going use by the application.
    This function must be executed before performing any operation on a
    wordpress blog.
    """
    global blog
    if blog is None:
        blog = _OwnBlog()
    else:
        _LOG.warning(
            "Attempt to initialize already initialized blog connection.")


class Blog:
    """
    Base blog object. Provides login handling, general class utilities and
    methods avalaible to use on any public Wordpress blog.
    """

    API = "/xmlrpc.php"

    def __init__(self, blog_address=None, custom_config=None):
        super().__init__()
        self._reqs_interval = 1  # minimal interval between subsequent reqests, in seconds
        self._last_req_ts = 0  # timestamp of the last request

        self._lock = threading.RLock()

        self.address = blog_address
        self.config_dict = custom_config or config.get_blog_config()
        self._iface = None
        self._login()

    def _call(self, method, use_requests=False, requests_resource=None):
        try:
            with self._lock:
                while (time.time() - self._last_req_ts) < self._reqs_interval:
                    # we should go to sleep for not too long because new
                    # reqest can arrive at any time so maybe it can happen
                    # that the timeout is just about to expire
                    time.sleep(self._reqs_interval/5)
                self._last_req_ts = time.time()

                if use_requests:
                    return getattr(requests, method)(requests_resource)
                else:
                    return self._iface.call(method)
        except OSError as exc:
            raise exceptions.BlogInternetError(exc) from exc
        except wordpress_xmlrpc.exceptions.InvalidCredentialsError as exc:
            raise exceptions.BlogAuthenticationError(exc) from exc
        except socket.timeout:
            raise
        except Exception as exc:
            raise exceptions.BlogMethodError(exc) from exc

    def _login(self):
        address = (self.address or self.config_dict["address"]) + self.API
        # authentication errors are never raised from here; socket related errors
        # can be raised on connection troubles; ServerConnectionError can be
        # raised by wordpress_xmlrpc on xmlrpc client ProtocolError but actually, on invalid
        # XML-RPC protocol, the OSError is raised by xmlrpc instead of the above
        try:
            self._last_req_ts = time.time()
            self._iface = wordpress_xmlrpc.Client(address,
                                                  self.config_dict["user_name"],
                                                  self.config_dict["password"])
        except OSError as exc:
            raise exceptions.BlogInternetError(exc) from exc
        except Exception as exc:
            raise exceptions.BlogMethodError(exc) from exc

    def add_comment(self, post_id, text):
        """
        Add comment to the given post.

        :param post_id: id of the post to add the comment to.
        :param text: text of the comment.
        """
        self._call(wordpress_xmlrpc.methods.comments.NewComment(
                    post_id, wordpress_xmlrpc.WordPressComment(
                        {"content": text})))


class _OwnBlog(Blog):
    """
    Blog that the user has an administrative access to.
    """

    USER_PHOTO_PATH = os.path.join(dirs.get_user_dir("pictures"),
                                   "blog_user_photo.jpg")

    def __init__(self, custom_config=None):
        self.max_posts = 1000
        self.max_comments = 1000
        self.about_me_page_title = "O mnie"  # displayed title of the "About me" page
        self.pending_post = None  # post instance being edited at a moment
        self.post_images = []  # list to store images to be attached to the current post
        super().__init__(custom_config=custom_config)
        if not self.get_about_me_page():
            self._create_about_me_page()
        self._cache_user_photo()

    def _create_about_me_page(self):
        page = wordpress_xmlrpc.WordPressPage()
        page.title = self.about_me_page_title
        page.content = ""
        self.publish_post(page)

    def _cache_user_photo(self):
        images = html_parsers.list_images(self.get_about_me_page().content)
        if len(images) > 0:
            photo_url = images[0]
            try:
                photo_bytes = self._call('get', True, photo_url).content
            except requests.exceptions.ConnectionError as e:
                _LOG.warning(e)
            else:
                if isinstance(photo_bytes, bytes):
                    photo_buffer = BytesIO(photo_bytes)
                    try:
                        image = Image.open(photo_buffer)
                        image.save(self.USER_PHOTO_PATH)
                    except OSError as e:
                        _LOG.error(e)
                else:
                    msg = "URL res with blog user photo does not contain" \
                          "proper bytes content."
                    _LOG.warning(msg)

    def publish_post(self, post):
        """
        Publish new post or update an existing one. If the given post already
        has an id assigned then it is just updated. Otherwise it is added
        as a new post. Post should consists of title and text.

        :param post: instance of the post to be published.
        """
        post.post_status = "publish"
        if not (hasattr(post, "post_type") and post.post_type == "page"):
            post.comment_status = "open"
        if hasattr(post, "id"):
            method = wordpress_xmlrpc.methods.posts.EditPost(post.id, post)
        else:
            method = wordpress_xmlrpc.methods.posts.NewPost(post)
        self._call(method)

    def attach_thumbnail(self, post, image_path):
        """
        Upload image to the server and attach it to the
        given post as a thumbnail. Post itself is not published.

        :param post: instance of the post.
        :param image_path: path to the image item in the file system.
        """
        if not hasattr(post, "id"):
            post.post_status = "draft"
            post_id = self._call(wordpress_xmlrpc.methods.posts.NewPost(post))
        else:
            post_id = post.id
        res = self._upload_media(image_path, post_id)
        post.thumbnail = res["id"]

    def attach_text(self, post, text):
        """
        Attach plain text to the given post.
        Keep all the previously embedded images intact.

        :param post: post instance.
        :param text: new post text.
        """
        post.content = html_parsers.embed_images(
            text, html_parsers.list_images(post.content))

    def attach_images(self, post):
        """
        Upload all images stored on the 'post_images' list to the
        server and attach them to the given post.

        :param post: instance of the post.
        """
        image_urls = []
        for image_path in self.post_images:
            # send image to the server
            image_urls.append(self._upload_media(image_path)["url"])
        post.content = html_parsers.embed_images(post.content, image_urls)
        self.post_images.clear()

    def _upload_media(self, media_path, post_id=None):
        data = {}
        if post_id:
            data["post_id"] = post_id
        data["name"] = os.path.basename(media_path)
        magician = magic.open(magic.MIME_TYPE | magic.SYMLINK)
        magician.load()
        data["type"] = magician.file(media_path)
        with open(media_path, "rb") as file:
            data["bits"] = wordpress_xmlrpc.compat.xmlrpc_client.Binary(
                file.read())
        return self._call(wordpress_xmlrpc.methods.media.UploadFile(data))

    def update_about_me_bio(self, text):
        """
        Update about me page with informations about the author.

        :param text: content of the page, eg. the author bio.
        """
        page = self.get_about_me_page()
        images = html_parsers.list_images(page.content)
        if len(images) > 0:
            text = html_parsers.embed_images(text, images[0])
        page.content = text
        self.publish_post(page)

    def update_about_me_photo(self, photo_path):
        """
        Update about me page with the author photo.

        :param photo_path: path to the new about me photo.
        """
        page = self.get_about_me_page()
        res = self._upload_media(photo_path)
        content = html_parsers.delete_images(page.content)
        page.content = html_parsers.embed_images(content, res["url"])
        self.publish_post(page)
        self._cache_user_photo()

    def get_about_me_page(self):
        """
        Get page with informations about me.

        :return: instance of the about me page.
        """
        page_list = self._call(wordpress_xmlrpc.methods.posts.GetPosts(
            {'post_type': 'page', 'title': self.about_me_page_title,
             'number': 1}))
        return page_list[0] if page_list else None

    def delete_post(self, post):
        """
        Delete post.

        :param post: post to be deleted.
        """
        self._call(wordpress_xmlrpc.methods.posts.DeletePost(post.id))

    def prepare_empty_post(self):
        """
        Prepare an empty post instance that can be filled with content and
        eventually published on the blog.
        """
        self.pending_post = wordpress_xmlrpc.WordPressPost()
        self.pending_post.content = ""

    def get_all_posts(self):
        """
        Get all the posts that have been published on the blog so far.

        :return: list of posts sorted by date of the publication.
        """
        return self._call(wordpress_xmlrpc.methods.posts.GetPosts(
                {'number': self.max_posts,  'orderby': 'post_date',
                 'order': 'DESC'}))

    def get_many_posts(self, offset, number):
        """
        Retrieve many posts.

        :param offset: offset from which posts should be taken.
        :param number: number of posts to retrieve.

        :return: list of posts.
        """
        return self._call(wordpress_xmlrpc.methods.posts.GetPosts(
                {'offset': offset, 'number': number, 'orderby': 'post_date',
                 'order': 'DESC'}))

    def get_all_comments_for_post(self, post_id):
        """
        Get all comments for the given post.

        :param post_id: id of the post to retrieve comments for.

        :return: list of comment instances sorted by the creation date.
        """
        return self._call(wordpress_xmlrpc.methods.comments.GetComments(
                {"post_id": post_id, 'orderby': 'date_created',
                    'order': 'DESC', 'number': self.max_comments}))

    def delete_comment(self, comment_id):
        """
        Delete comment with the given id.

        :param comment_id: id of the comment to be deleted.
        """
        self._call(wordpress_xmlrpc.methods.comments.DeleteComment(comment_id))

    def edit_user_profile(self, desc):
        """
        Update user profile.

        :param desc: dictionary with attributes to be applied to the user profile.
        """
        profile = self._call(wordpress_xmlrpc.methods.users.GetProfile())
        for attribute, value in desc.items():
            if hasattr(user, attribute):
                setattr(user, attribute, value)
            else:
                _LOG.warning(
                    "User profile has no attribute {}".format(attribute))
        self._call(wordpress_xmlrpc.methods.users.EditProfile(profile))

    def get_user(self, user_id):
        """
        Retrieve user with the given id.

        :param id: id of a user.

        :return: instance of a user.
        """
        return self._call(wordpress_xmlrpc.methods.users.GetUser(user_id))

    def compose_post_view(self, post):
        """
        Compose and arrange all the post elements into a single html document.

        :param post: post instance.

        :return: properly constructed post view.
        """
        line_break = "<br>"
        space = 2 * line_break
        mark = '<div class="published">' + 'Post opublikowany  ' + \
               str(post.date) + '</div>'
        doc = [post.title, post.content, mark]
        all_comments = self.get_all_comments_for_post(post.id)
        if all_comments:
            wrote = "  napisał/a:"
            comments_header = "KOMENTARZE({}):".format(len(all_comments))
            comments_arranged = space.join([
                line_break.join(['<div class="date">' + \
                                 str(comment.date_created) + \
                                 '</div>' + '<div class="comment_author">' +\
                                 comment.author + wrote + '</div>' + \
                                 '<div class="comment">' + comment.content +\
                                 '</div>']) for comment in all_comments])
            comments = '<div class="comments">' + \
                       space.join([comments_header, comments_arranged]) + \
                       '</div>'
            doc.append(comments)
        return space.join(doc)
