# Project modules
from config import config

# 3rd party modules
import flask

# stdlib
import secrets, logging, ipaddress

log = logging.getLogger('redditarchiver_main')


def manage_cookie():
    """
    Checks if the cookie is correctly set. If not, creates it.
    """
    try:
        cookie = flask.request.cookies['redditarchive_id']
        flask.g.cookie = cookie
    except:
        # cookie does not exist, let us generate an ID
        random_id = secrets.token_urlsafe(32)
        flask.g.cookie = random_id
        flask.g.resp.set_cookie('redditarchive_id', random_id, max_age=365*24*60*60, samesite="Lax")
        log.info(f"Client does not have cookie: sending cookie {random_id}")


def is_client_allowed(source_ip):
    """
    If app.only-allow-from in config is defined, check if the IP is allowed to use the site.
    """
    only_allow_from = config['app'].get('only-allow-from', None)
    if not only_allow_from:
        return True
    else:
        for network in only_allow_from:
            if ipaddress.ip_address(source_ip) in ipaddress.ip_network(network):
                return True
        else:
            return False
