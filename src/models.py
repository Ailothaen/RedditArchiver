# stdlib
import sqlite3, datetime, os, statistics


def create():
    """
    Create the sqlite database if it does not exist
    """
    base = sqlite3.connect("data/redditarchiver.sqlite3")
    cursor = base.cursor()
    cursor.execute('CREATE TABLE "tokens" ("id" TEXT, "ip" TEXT, "created_at" INTEGER, "last_seen_at" INTEGER, "token" TEXT, PRIMARY KEY("id"))')
    cursor.execute('CREATE TABLE "jobs" ("id" TEXT, "started_at" INTEGER, "finished_at" INTEGER, "submission" TEXT, "nb_replies" INTEGER, "requestor" TEXT, "status" TEXT, "failure_reason" INTEGER, "filename" TEXT, PRIMARY KEY("id"), FOREIGN KEY("requestor") REFERENCES "tokens"("id"))')
    base.commit()
    base.close()


def connect():
    """
    Connects to sqlite database

    Returns a tuple with base and cursor, to be used in all other functions
    """
    if not os.path.exists("data/redditarchiver.sqlite3"):
        create()
    base = sqlite3.connect("data/redditarchiver.sqlite3")
    base.row_factory = sqlite3.Row # having column names! cf https://stackoverflow.com/a/18788347
    cursor = base.cursor()
    return (base, cursor)


def create_job(model, job_id, submission, requestor):
    """
    Adds a job in database.
    """
    model[1].execute('INSERT INTO jobs VALUES (:job_id, NULL, NULL, :submission, NULL, :requestor, "created", NULL, NULL)', {'job_id': job_id, 'submission': submission, 'requestor': requestor})
    model[0].commit()


def read_job(model, job_id):
    """
    Returns the data of a job from database.
    """
    model[1].execute('SELECT * FROM jobs WHERE id=:job_id', {'job_id': job_id})
    result = model[1].fetchall()
    if result:
        return result[0]
    else:
        return "notfound"


def start_job(model, job_id):
    """
    Mark a job as started in database.
    """
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    model[1].execute('UPDATE jobs SET status="ongoing", started_at=:started_at WHERE id=:job_id', {'job_id': job_id, 'started_at': now})
    model[0].commit()


def mark_job_success(model, job_id, filename=None):
    """
    Mark a job as successful in database.
    """
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    model[1].execute('UPDATE jobs SET status="success", filename=:filename, finished_at=:finished_at WHERE id=:job_id', {'job_id': job_id, 'filename': filename, 'finished_at': now})
    model[0].commit()


def mark_job_failure(model, job_id, reason=None):
    """
    Mark a job as failed in database.
    """
    model[1].execute('UPDATE jobs SET status="failure", failure_reason=:failure_reason WHERE id=:job_id', {'job_id': job_id, 'failure_reason': reason})
    model[0].commit()


def write_nb_replies(model, job_id, nb_replies=None):
    """
    Write the number of replies in a submission in database (useful for ETA calculation)
    """
    model[1].execute('UPDATE jobs SET nb_replies=:nb_replies WHERE id=:job_id', {'job_id': job_id, 'nb_replies': nb_replies})
    model[0].commit()


def create_token(model, cookie, token):
    """
    Creates a token (connection to Reddit API) in database
    """
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    model[1].execute('INSERT INTO tokens VALUES (:id, NULL, :created_at, :last_seen_at, :token)', {'id': cookie, 'created_at': now, 'last_seen_at': now, 'token': token})
    model[0].commit()


def read_token(model,  cookie):
    """
    Reads a token (connection to Reddit API) from database
    """
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    model[1].execute('SELECT token FROM tokens WHERE id=:id', {'id': cookie})
    result = model[1].fetchall()
    if result:
        token = result[0]['token']
        # mark token as freshly read
        model[1].execute('UPDATE tokens SET last_seen_at=:last_seen_at WHERE id=:id', {'id': cookie, 'last_seen_at': now})
        model[0].commit()
        return token
    else:
        return None


def cleanup_sessions(model):
    """
    Remove all tokens unused since 3 months
    """
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    model[1].execute('DELETE FROM tokens WHERE (:now - last_seen_at) > 7760000', {'now': now})
    model[0].commit()


def calculate_average_eta(model):
    """
    Calculates average time to download a thread (depending on the number of replies) so we can give a good ETA estimation.
    """
    model[1].execute('SELECT started_at, finished_at, nb_replies FROM jobs WHERE status = "success" ORDER BY finished_at DESC LIMIT 100')
    result = model[1].fetchall()
    if len(result) == 0:
        return None
    else:
        times = []
        for line in result:
            duration = line['finished_at']-line['started_at']
            if duration == 0:
                duration = 1
            times.append(line['nb_replies']/duration)
        return statistics.median(times)
