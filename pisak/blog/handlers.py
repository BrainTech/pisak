"""
Library of blog application specific signal handlers.
"""
from pisak import signals

from pisak.blog import wordpress


@signals.registered_handler("blog/attach_post_content")
def attach_post_content(text_field):
    """
    Attach content to the currenlty edited post.

    :param text_field: text field that contains a content for the currently
    edited post
    """
    post = wordpress.blog.pending_post
    if post is not None:
        wordpress.blog.attach_text(post, text_field.get_text())


@signals.registered_handler("blog/attach_post_title")
def attach_post_title(text_field):
    """
    Attach title to the currenlty edited post.

    :param text_field: text field that contains a title for the currently
    edited post
    """
    post = wordpress.blog.pending_post
    if post is not None:
        post.title = text_field.get_text()


@signals.registered_handler("blog/publish_pending_post")
def publish_pending_post(source):
    """
    Publish the currently edited post.
    """
    wordpress.blog.attach_images(wordpress.blog.pending_post)
    wordpress.blog.publish_post(wordpress.blog.pending_post)
    wordpress.blog.pending_post = None


@signals.registered_handler("blog/delete_pending_post")
def delete_pending_post(source):
    """
    Permanently delete the currently edited post from the blog.
    """
    if wordpress.blog.pending_post:
        wordpress.blog.delete_post(wordpress.blog.pending_post)
        wordpress.blog.pending_post = None


@signals.registered_handler("blog/publish_about_me_bio")
def publish_about_me_bio(text_field):
    """
    Publish about me informations.

    :param text_field: text field that contains about me informations
    """
    wordpress.blog.update_about_me_bio(text_field.get_text())


def publish_about_me_photo(photo_path):
    """
    Publish my photo on the about me page.

    :param photo_path: photo path
    """
    wordpress.blog.update_about_me_photo(photo_path)


@signals.registered_handler("blog/next_post")
def next_post():
    """
    Move to the view of the next post.
    """
    pass


@signals.registered_handler("blog/previous_post")
def previous_post():
    """
    Move to the view of the previous post.
    """
    pass


@signals.registered_handler("blog/scroll_post_up")
def scroll_post_up(post):
    """
    Scroll post upward. 
    
    :param post: post to be scrolled
    """
    post.v_adj.set_value(post.v_adj.get_value() - post.v_adj.get_page_size()/2)

@signals.registered_handler("blog/scroll_post_down")
def scroll_post_down(post):
    """
    Scroll post downward. 
    
    :param post: post to be scrolled
    """
    post.v_adj.set_value(post.v_adj.get_value() + post.v_adj.get_page_size()/2)

@signals.registered_handler("blog/go_back")
def go_back(post):
    """
    Go backward in the site. 
    
    :param view: view to be changed
    """
    post.view.go_back()

@signals.registered_handler("blog/go_forward")
def go_forward(post):
    """
    Go forward in the site. 
    
    :param view: view to be changed
    """
    post.view.go_forward()
