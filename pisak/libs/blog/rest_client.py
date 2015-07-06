import requests

from pisak import logger
from pisak.libs.blog import exceptions, config


_LOG = logger.get_logger(__name__)


class Blog(object):
    """
    Client of a blog that makes a JSON API avalaible.

    :param address: blog's site domain (string) or ID (integer).
    """
    def __init__(self, address):
        self.max_posts = 100  # api's max
        self.max_comments = 100  # api's max
        self.address_base = "https://public-api.wordpress.com/rest/v1.1/sites/"
        self.address = self.address_base + str(address).replace("/", "%2F")

    def _get(self, resource):
        try:
            return requests.get(self.address + resource).json()
        except requests.exceptions.ConnectionError as exc:
            raise exceptions.BlogInternetError(exc) from exc
        except Exception as exc:
            raise exceptions.BlogMethodError(exc) from exc

    def get_all_posts(self):
        """
        Get all posts from the blog.

        :returns: list of all posts. Each post is a dictionary.
        """
        return self._get(
            "/posts/?number={}".format(str(self.max_posts)))["posts"]

    def get_post(self, ide):
        """
        Get single post from the blog.

        :param ide: id of a post to be returned.

        :returns: single post. Post is a dictionary.
        """
        return self._get("/posts/{}".format(str(ide)))

    def get_comment(self, ide):
        """
        Get single comment.

        :param ide: id of the comment to be returned.

        :returns: single comment. Comment is a dictionary.
        """
        return self._get("/comments/{}".format(str(ide)))
        
    def get_comments_for_post(self, post_ide):
        """
        Get all comments for the given post.

        :param post_ide: id of the post.

        :returns: list of all comments for the given post.
        Each comment is a dictionary
        """
        return self._get(
            "/posts/{}/replies/?number={}".format(
                str(post_ide), str(self.max_comments)))["comments"]

    def compose_post_view(self, post):
        """
        Compose and arrange all the post elements into a single html document.

        :param post: post instance

        :returns: properly constructed post view
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
