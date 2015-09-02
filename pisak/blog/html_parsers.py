from bs4 import BeautifulSoup


def apply_linebreaks(text):
    """
    Convert python-style linebreaks to a html-style ones.
    
    :param text: text with python-style linebreaks

    :returns: text with html-style linebreaks
    """
    line_break = "<br>"
    return text.replace("\n", line_break)


def apply_paragraphs(text):
    """
    Apply html-style paragraphs to the text.
    
    :param text: text with python-style or no paragraphs

    :returns: text with html-style paragraphs
    """
    paragraph_start = "<p>"
    paragraph_end = "</p>"
    text = paragraph_start + text + paragraph_end
    text.replace("\n\n", paragraph_end + paragraph_start)
    return text


def embed_images(content, image_urls):
    """
    Embed img tag with image url into the html content.

    :param content: html text
    :param image_urls: url to the image or list of urls

    :returns: content with img tag embedded
    """
    line_break = "<br>"
    separator = 2 * line_break
    if isinstance(image_urls, str):
        image_urls = [image_urls]
    image_urls = ["<img src='{}' >".format(image_url) for image_url in image_urls]
    return content + separator + separator.join(image_urls)


def delete_images(content):
    """
    Remove all the img tags.

    :param content: html text

    :returns: content with img tags removed
    """
    parser = BeautifulSoup(content)
    for img in parser.find_all("img"):
        img.replace_with("")
    return parser.prettify()


def list_images(content):
    """
    Extract and list all images in a html text.

    :param content: html text

    :returns: list of image urls
    """
    return [img.get("src") for img in
            BeautifulSoup(content).find_all("img")]


def extract_text(content):
    """
    Get all plain text from a html document.

    :param content: html text

    :returns: plain text
    """
    parser = BeautifulSoup(content)
    convert_linebreaks(parser)
    return parser.get_text().strip()


def convert_linebreaks(parser):
    """
    Converts all html-style linebreaks to the python-style ones.

    :param parser: beautiful soup parser
    """
    for break_line in parser.find_all("br"):
        break_line.replace_with("\n")
