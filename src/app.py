# Project modules
import auth, controllers, models
from config import config

# 3rd party modules
import flask, flask_apscheduler

# stdlib
import logging, os, datetime

app = flask.Flask(__name__)
log = logging.getLogger('redditarchiver_main')


@app.before_request
def before_request_callback():
    """
    Initialises cookie and Reddit token
    """
    # Preventing unauthorized people to access the app
    if config["docker"]:
        # No easy way to use X-Forwarded-For inside a Docker container, from what I know.
        # If you do know, your help is welcome!
        pass
    else:
        client_ip = flask.request.headers.getlist("X-Forwarded-For")[0]
        is_allowed = auth.is_client_allowed(client_ip)
        if not is_allowed:
            log.warning(f"Access denied from {client_ip}")
            flask.abort(403)

    flask.g.db = models.connect()
    flask.g.resp = flask.make_response()
    flask.g.data = {}

    # Manage cookies
    if flask.request.endpoint not in ('token', 'favicon', 'status', 'download'):
        auth.manage_cookie()
        flask.g.token = models.read_token(flask.g.db, flask.g.cookie)



# -------------------------- #
# Routes                     #
# -------------------------- #

@app.route("/")
def main():
    """
    Landing page, where the form to download is.
    If the user is not authenticated, a prompt to authenticate appears instead
    """
    if flask.g.token is None:
        # Authentication URL crafter
        flask.g.data['auth_url'] = controllers.craft_authentication_url()
        flask.g.resp.data = flask.render_template('main_unauthenticated.html', data=flask.g.data, config=config)
    else:
        flask.g.resp.data = flask.render_template('main_authenticated.html', data=flask.g.data, config=config)
    return flask.g.resp


@app.route("/favicon.ico")
def favicon():
    """
    Self-explanatory, I guess?
    """
    return flask.send_from_directory(os.path.join(os.getcwd(), 'static', 'images'), 'favicon.ico')


@app.route("/token")
def token():
    """
    Interception of token given by Reddit
    """
    cookie = flask.request.args.get('state')
    try:
        refresh_token = controllers.get_refresh_token()
    except:
        log.error(f'Reddit did not recognize the code for {cookie}')
        return "Reddit did not recognize the code given. This should not happen.", 400

    log.info(f'Refresh token got for cookie {cookie}: {refresh_token}')
    models.create_token(flask.g.db, cookie, refresh_token)

    # taking back to homepage
    return flask.redirect("/", code=303)


@app.route("/request", methods=['POST'])
def request():
    """
    Requests a job
    """
    try:
        flask.g.data['job_id'] = controllers.request()
    except ValueError as e:
        flask.g.data['error_message'] = controllers.error_message(str(e))
        flask.g.resp.data = flask.render_template('request_error.html', data=flask.g.data, config=config)
    else:
        flask.g.resp.data = flask.render_template('request.html', data=flask.g.data, config=config)
    
    return flask.g.resp


@app.route("/status/<job_id>")
def status(job_id):
    """
    Requests the status of a job
    """
    flask.g.resp.status, flask.g.resp.data = controllers.status(job_id)
    return flask.g.resp


@app.route("/download/<job_id>")
def download(job_id):
    """
    Downloads the result of a job
    """
    log.info(f"Download requested for job {job_id}")
    filename = controllers.get_filename(job_id)
    
    return flask.send_from_directory(os.path.join(os.getcwd(), 'output'), filename, as_attachment=True)



# -------------------------- #
# Schedulers                 #
# -------------------------- #

scheduler = flask_apscheduler.APScheduler()
scheduler.init_app(app)
scheduler.start()

@scheduler.task('interval', id='st_cleanup_downloads', hours=1)
def cleanup_downloads():
    """
    Remove all downloads older than 24 hours
    """
    controllers.cleanup_downloads()


@scheduler.task('interval', id='st_cleanup_sessions', hours=24)
def cleanup_sessions():
    """
    Remove all sessions unused since 3 months
    """
    controllers.cleanup_sessions()


@scheduler.task('interval', id='st_calculate_average_eta', hours=24, start_date=datetime.datetime.now()+datetime.timedelta(seconds=10))
def calculate_average_eta():
    """
    Calculates average time to download a thread (depending on the number of replies) so we can give a good ETA estimation.
    Runs at startup then once every 24h.
    """
    controllers.calculate_average_eta()
