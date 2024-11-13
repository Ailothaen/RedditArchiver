# stdlib
import re


def extract_id(url):
    """
    Extracts the submission ID from a supplied URL
    """
    regexes = (r"^([a-z0-9]+)/?$",
    r"^https?:\/\/(?:old|new|www)?\.reddit\.com\/([a-z0-9]+)\/?$",
    r"^https?:\/\/(?:old|new|www)?\.reddit\.com\/r\/[a-zA-Z0-9\-_]+\/comments\/([a-z0-9]+)\/?")

    for regex in regexes:
        result = re.search(regex, url)
        if result is not None:
            return result.group(1)
