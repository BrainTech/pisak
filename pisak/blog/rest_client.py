"""
Wordpress JSON REST API client implementation.
"""
import socket
import time
from threading import RLock
import requests

from pisak import logger, blog
from pisak.blog import exceptions, config


_LOG = logger.get_logger(__name__)


class Blog:
    """
    Client of a blog that makes a JSON API avalaible.

    :param address: blog's site domain (string) or ID (integer).
    """
    def __init__(self, address):
        self._reqs_interval = 1  # minimal interval between subsequent reqests, in seconds
        self._last_req_ts = 0  # timestamp of the last request

        self._lock = RLock()

        self.max_posts = 100  # api's max
        self.max_comments = 100  # api's max
        self.address_base = "https://public-api.wordpress.com/rest/v1.1/sites/"
        self.address = self.address_base + str(address).replace("/", "%2F")

    def _get(self, resource):
        try:
            with self._lock:
                while (time.time() - self._last_req_ts) < self._reqs_interval:
                    # we should go to sleep for not too long because new
                    # reqest can arrive at any time so maybe it can happen
                    # that the timeout is just about to expire
                    time.sleep(self._reqs_interval/5)
                self._last_req_ts = time.time()

                return requests.get(self.address + resource).json()
        except requests.exceptions.ConnectionError as exc:
            raise exceptions.BlogInternetError(exc) from exc
        except socket.timeout:
            raise
        except Exception as exc:
            raise exceptions.BlogMethodError(exc) from exc

    def get_all_posts(self):
        """
        Get all posts from the blog.

        :return: list of all posts. Each post is a dictionary.
        """
        res = self._get(
            "/posts/?number={}".format(str(self.max_posts)))
        return res['posts'] if 'posts' in res else []

    def get_many_posts(self, offset, number):
        """
        Retrieve many posts.

        :param offset: offset from which posts should be taken.
        :param number: number of posts to retrieve.

        :return: list of posts.
        """
        res = self._get(
            "/posts/?offset={}?number={}".format(str(offset), str(number)))
        return res['posts'] if 'posts' in res else []

    def get_post(self, ide):
        """
        Get single post from the blog.

        :param ide: id of a post to be returned.

        :return: single post. Post is a dictionary.
        """
        return self._get("/posts/{}".format(str(ide)))

    def get_comment(self, ide):
        """
        Get single comment.

        :param ide: id of the comment to be returned.

        :return: single comment. Comment is a dictionary.
        """
        return self._get("/comments/{}".format(str(ide)))
        
    def get_comments_for_post(self, post_ide):
        """
        Get all comments for the given post.

        :param post_ide: id of the post.

        :return: list of all comments for the given post.
        Each comment is a dictionary
        """
        res = self._get(
            "/posts/{}/replies/?number={}".format(
                str(post_ide), str(self.max_comments)))
        return res['comments'] if 'comments' in res else []

    def compose_post_view(self, post):
        """
        Compose and arrange all the post elements into a single html document.

        :param post: post instance

        :return: properly constructed post view
        """
        line_break = "<br>"
        space = 2 * line_break
        mark = '<div class="published">' + 'Post opublikowany  ' + \
               post["date"] + '</div>' + '<div class="author">' + \
               "Autor: " + post["author"]["name"] + '</div>'
        doc = [post["title"], post["content"], mark]
        all_comments = self.get_comments_for_post(post["ID"])
        if all_comments:
            wrote = "  napisał/a  "
            comments_header = "KOMENTARZE({}):".format(len(all_comments))
            comments_arranged = space.join([
                line_break.join(['<div class="date">' + comment["date"] + \
                                 '</div>' + '<div class="comment_author">' + \
                                 comment["author"]["name"]  + wrote + \
                                 '</div>' + '<div class="comment">' + \
                                 comment["content"] + \
                                 '</div>']) for comment in all_comments])
            comments = '<div class="comments">' + \
                       space.join([comments_header, comments_arranged]) + \
                       '</div>'
            doc.append(comments)
        return space.join(doc)
