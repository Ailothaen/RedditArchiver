# Project modules
import downloader, models, utils
from config import config

# 3rd party modules
import flask, praw

# stdlib
import threading, secrets, logging, json, datetime, os

log = logging.getLogger('redditarchiver_main')


def request():
    """
    Initiates a submission-saving request (= job)
    """
    job_id = secrets.token_urlsafe(16)
    submission = flask.request.form.get("submission-id")

    submission_id = utils.extract_id(submission)
    if submission_id is None:
        log.error(f'{job_id}: URL not valid ({submission})')
        raise ValueError("BAD_URL")

    models.create_job(flask.g.db, job_id, submission_id, flask.g.cookie)

    worker = threading.Thread(target=downloader.main, args=(submission_id, flask.g.token, job_id))
    worker.name = job_id
    worker.daemon = True

    log.info(f'{job_id}: Job starting (submission {submission_id}, token {flask.g.token})')
    worker.start()
    
    return job_id


def craft_authentication_url():
    """
    Makes the authentication URL, for the user to allow Reddit to read submissions through their account
    """
    reddit = praw.Reddit(client_id=config['reddit']['client-id'], client_secret=config['reddit']['client-secret'], redirect_uri=f"{config['app']['url']}/token", user_agent=config['reddit']['agent'])
    return reddit.auth.url(duration="permanent", scopes=['read'], state=flask.g.cookie)


def get_refresh_token():
    """
    Gets refresh token from the code given by Reddit
    (more info: https://praw.readthedocs.io/en/stable/getting_started/authentication.html)
    """
    code = flask.request.args.get('code')
    reddit = praw.Reddit(client_id=config['reddit']['client-id'], client_secret=config['reddit']['client-secret'], redirect_uri=f"{config['app']['url']}/token", user_agent=config['reddit']['agent'])
    return reddit.auth.authorize(code)


def status(job_id):
    """
    Queries the current status of a job.
    """
    job = models.read_job(flask.g.db, job_id)
    data = json.dumps({"status": job['status'], "error_message": error_message(job['failure_reason']), "eta": calculate_estimated_time(job['started_at'], job['nb_replies'], config['runtime']['average'])})
    
    if job['status'] == "ongoing":
        status = 409
    elif job['status'] == "failure":
        status = 404
    elif job['status'] == "success":
        status = 200
    elif job['status'] == "notfound":
        status = 404

    return status, data


def calculate_estimated_time(start_time, nb_replies, average):
    """
    Tries to do an estimation on the remaining time - based on the average time of previous jobs.
    """
    if nb_replies is None:
        return None
    
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    elapsed = now-start_time
    estimated_total = nb_replies/average
    estimated_remaining = int(estimated_total-elapsed)

    if estimated_remaining < 0:
        return "It seems that the retrieval is taking a bit more time than expected. Please stand by..."
    elif estimated_remaining < 10:
        return "Estimated remaining time: less than 10 seconds"
    elif estimated_remaining < 60:
        return f"Estimated remaining time: {estimated_remaining} seconds"
    else:
        m, s = divmod(estimated_remaining, 60)
        return f"Estimated remaining time: {m} minutes, {s} seconds"


def get_filename(job_id):
    """
    Get filename of a downloaded submission (taking job ID as input)
    """
    job = models.read_job(flask.g.db, job_id)
    return job["filename"]


def error_message(reason):
    """
    Returns the proper error message from a reason
    """
    if reason == 'SUBMISSION_NOT_FOUND':
        message = "The submission could not be found. Please check if the submission (still) exists."
    elif reason == 'BAD_AUTHENTICATION':
        message = "It looks like your Reddit account does no longer allow Reddit Archiver to read Reddit on its behalf. Please try to allow it again by clicking here. If it still does not work, please <a href=\""+config['app']['project']+"\" target=\"_blank\">open an issue on the GitHub</a>."
    elif reason == 'BAD_URL':
        message = "The link you provided is not a valid Reddit submission. Please check it and submit it again."
    elif reason == 'BAD_PERMISSIONS':
        message = "Your request cannot be completed because of an issue in the server. Please contact the administrator and tell them to look in the error logs. If you are the administrator and cannot resolve the problem, please <a href=\""+config['app']['project']+"\" target=\"_blank\">open an issue on the GitHub</a>."
    elif reason == 'UNKNOWN':
        message = "Your request cannot be completed because of an issue in the server. Please contact the administrator and tell them to look in the error logs. If you are the administrator and cannot resolve the problem, please <a href=\""+config['app']['project']+"\" target=\"_blank\">open an issue on the GitHub</a>."
    else:
        message = None
    return message


def cleanup_downloads():
    """
    Remove all files in output older than 24 hours
    """
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    files = os.listdir('output')
    for file in files:
        mtime = os.path.getmtime(os.path.join('output', file))
        if (now-mtime) > 86400:
            os.remove(os.path.join('output', file))


def cleanup_sessions():
    """
    Remove all sessions unused since 3 months
    """
    db = models.connect()
    models.cleanup_sessions(db)


def calculate_average_eta():
    """
    Calculates average time to download a thread (depending on the number of replies) so we can give a good ETA estimation.
    """
    db = models.connect()
    average = models.calculate_average_eta(db)
    if average is None:
        log.info(f"Cannot calculate average, default value of 30 is going to be taken")
        config['runtime']['average'] = 30
    else:
        config['runtime']['average'] = int(average)
        log.info(f"New average was calculated: new value is {config['runtime']['average']}")
