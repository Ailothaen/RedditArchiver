# Project modules
from sqlite3 import connect
from config import config
import models

# 3rd party modules
from anytree import Node, PreOrderIter
from anytree import util as anytree_util
import praw, prawcore, markdown2

# stdlib
import datetime, os, logging, sys

log = logging.getLogger('redditarchiver_main')


# -------------------------- #
# Functions                  #
# -------------------------- #

def commentParser(initialText):
    """
    Parses Reddit's pseudo-markdown into HTML formatting
    """
    # removing HTML characters
    text = initialText.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    # transforming markdown to HTML
    text = markdown2.markdown(text)

    # converting linebreaks to HTML
    text = text.replace('\n\n', '</p><p>')
    text = text.replace('\n', '<br>')
    
    # removing the last <br> that is here for a weird reason
    if text[-4:] == '<br>':
        text = text[:-4]

    return text


def connect_to_submission(submission_id, token):
    """
    Initiates "connection" to submission and returns the submission object.
    """
    reddit = praw.Reddit(client_id=config['reddit']['client-id'], client_secret=config['reddit']['client-secret'], refresh_token=token, user_agent=config['reddit']['agent'])
    submission = reddit.submission(id=submission_id)
    log.info(f'Submission ID: {submission_id}')
    nb_replies = submission.num_comments
    return submission, nb_replies


def download_submission(submission, submission_id):
    """
    Retrieves the submission and its comments from Reddit API.
    Returns two lists, one being a flat list of comments with their attributes (comments_forest), the other one being the tree structure of the submission (comments_index)
    """
    # Contains all the node objects (for the tree structure)
    comments_index = {}
    # Contains all the comment objects
    comments_forest = {}

    # Creating root node: the submission itself
    comments_index['t3_'+submission_id] = Node('t3_'+submission_id)

    # Getting all comments in tree order, according to the sorting algorithm defined.
    # See https://praw.readthedocs.io/en/latest/tutorials/comments.html#extracting-comments
    submission.comments.replace_more(limit=None)

    # Filling index and forest
    comment_queue = submission.comments[:] 
    while comment_queue:
        comment = comment_queue.pop(0)
        comments_index['t1_'+comment.id] = Node('t1_'+comment.id, parent=comments_index[comment.parent_id])
        comments_forest['t1_'+comment.id] = {'a': '(deleted)' if comment.author is None else comment.author.name, 'b': '(deleted)' if comment.body is None else comment.body, 'd': comment.distinguished, 'e': comment.edited, 'l': comment.permalink ,'o': comment.is_submitter, 's': comment.score, 't': comment.created_utc}
        comment_queue.extend(comment.replies)

    return submission, comments_index, comments_forest


def generate_html(submission, submission_id, now_str, sort, comments_index, comments_forest):
    """
    Generates HTML structure with the submission, its replies and all its info in it.
    Note: As now, "sort" is unused. Todo?
    """
    # Beginning of file, with <head> section
    html_head = f"""<!doctype html><html><head><meta charset="utf-8"/><title>{submission.subreddit.display_name} – {submission.title}</title><style>html{{font-family: 'Arial', 'Helvetica', sans-serif;font-size: 15px;box-sizing: border-box;}}div{{margin: 0px -5px 0px 0px;padding: 5px;}}header{{font-weight: bold;}}.f{{margin-top: 15px;}}.o{{background-color: #eaeaea;}}.e{{background-color: #fafafa;}}.l1{{border-left: 4px solid #3867d6;}}.l1 > header, .l1 > a, .l1 > header a{{color: #3867d6;}}.l2{{border-left: 4px solid #e74c3c;}}.l2 > header, .l2 > a, .l2 > header a{{color: #e74c3c;}}.l3{{border-left: 4px solid #20bf6b;}}.l3 > header, .l3 > a, .l3 > header a{{color: #20bf6b;}}.l4{{border-left: 4px solid #f7b731;}}.l4 > header, .l4 > a, .l4 > header a{{color: #f7b731;}}.l5{{border-left: 4px solid #9b59b6;}}.l5 > header, .l5 > a, .l5 > header a{{color: #9b59b6;}}.l6{{border-left: 4px solid #fa8231;}}.l6 > header, .l6 > a, .l6 > header a{{color: #fa8231;}}.l7{{border-left: 4px solid #a5b1c2;}}.l7 > header, .l7 > a, .l7 > header a{{color: #a5b1c2;}}.l8{{border-left: 4px solid #4b6584;}}.l8 > header, .l8 > a, .l8 > header a{{color: #4b6584;}}.l9{{border-left: 4px solid #0fb9b1;}}.l9 > header, .l9 > a, .l9 > header a{{color: #0fb9b1;}}.l0{{border-left: 4px solid #fd79a8;}}.l0 > header, .l0 > a, .l0 > header a{{color: #fd79a8;}}.m{{background-color: #c8ffc8;}}.a{{background-color: #ffdcd2;}}.p{{background-color: #b4c8ff;}}.n{{text-decoration: none;}}.D{{cursor:not-allowed!important;color:#ccc!important;}}</style></head><body>"""

    # Header of file, with submission info
    html_submission = f"""<h1><a href="{config['reddit']['root']}/r/{submission.subreddit.display_name}/">/r/{submission.subreddit.display_name}</a> – <a href="{config['reddit']['root']}{submission.permalink}">{submission.title}</a></h1><h2>Snapshot taken on {now_str}<br/>Posts: {submission.num_comments} – Score: {submission.score} ({int(submission.upvote_ratio*100)}% upvoted) – Flair: {'None' if submission.link_flair_text is None else submission.link_flair_text} – Sorted by: {sort}<br/>Sticky: {'No' if submission.stickied is False else 'Yes'} – Spoiler: {'No' if submission.spoiler is False else 'Yes'} – NSFW: {'No' if submission.over_18 is False else 'Yes'} – OC: {'No' if submission.is_original_content is False else 'Yes'} – Locked: {'No' if submission.locked is False else 'Yes'}</h2><p><em>Snapshot taken from <a href="{config['app']['url']}">{config['app']['name']}</a> v{config['app']['version']}. All times are UTC.</em></p>"""

    # First comment (which is actually OP's post)
    html_firstpost = f"""<h3>Original post</h3><div class="b p f l1" id="t3_{submission_id}"><header><a href="{config['reddit']['root']}/u/{'(deleted)' if submission.author is None else submission.author.name}">{'(deleted)' if submission.author is None else submission.author.name}</a>, on {datetime.datetime.fromtimestamp(submission.created_utc).strftime(config["defaults"]["dateformat"])}</header>{commentParser(submission.selftext)}</div><h3>Comments</h3>"""

    # Iterating through the tree to put comments in right order

    html_comments = ''
    previous_comment_level = 1 # We begin at level 1.
    comment_counter = 1 # Comment counter

    #for comment in generator:
    for node in PreOrderIter(comments_index['t3_'+submission_id]):
        current_comment_level = node.depth
        current_comment_id = node.name

        if node.name[:2] == 't3': # root is the submission itself, we ignore it
            continue

        # We close as much comments as we need to.
        # Is this is a sibling (= same level), we just close one comment.
        # If this is on another branch, we close as much comments as we need to to close the branch.
        if current_comment_level <= previous_comment_level:
            for i in range(0, previous_comment_level-current_comment_level+1):
                html_comments += '</div>'

        # CSS classes to be applied.
        classes = ''

        # If first-level comment, we put a margin
        if current_comment_level == 1:
            classes += 'f '

        if comments_forest[current_comment_id]['d'] == 'admin':
            classes += 'a ' # Distinguished administrator post color
        elif comments_forest[current_comment_id]['d'] == 'moderator':
            classes += 'm ' # Distinguished moderator post color
        elif comments_forest[current_comment_id]['o']:
            classes += 'p ' #  OP post color
        elif current_comment_level % 2 == 0:
            classes += 'e ' # Even post color
        else:
            classes += 'o ' # Odd post color

        # Post level
        classes += 'l'+str(current_comment_level)[-1] # only taking the last digit
        html_comments += f'<div class="{classes}" id="{current_comment_id}">'

        # Getting parents and siblings for easy navigation
        try:
            previous_sibling = anytree_util.leftsibling(node).name
            previous_sibling_d = ''
        except AttributeError: # first sibling
            previous_sibling = ''
            previous_sibling_d = ' D' # class "disabled" for first and last siblings

        try:
            next_sibling = anytree_util.rightsibling(node).name
            next_sibling_d = ''
        except AttributeError: # last sibling
            next_sibling = ''
            next_sibling_d = ' D'

        parent = node.parent.name

        time_comment = datetime.datetime.fromtimestamp(comments_forest[current_comment_id]['t'])
        time_comment_str = time_comment.strftime(config["defaults"]["dateformat"])

        # Adding the comment to the list
        html_comments += f"""<header><a href="{config['reddit']['root']}/u/{comments_forest[current_comment_id]['a']}">{comments_forest[current_comment_id]['a']}</a>, on <a href="{config['reddit']['root']}{comments_forest[current_comment_id]['l']}">{time_comment_str}</a> ({comments_forest[current_comment_id]['s']}{'' if comments_forest[current_comment_id]['e'] is False else ', edited'}) <a href="#{parent}" class="n P">▣</a> <a href="#{previous_sibling}" class="n A{previous_sibling_d}">🠉</a> <a href="#{next_sibling}" class="n B{next_sibling_d}">🠋</a> <a href="#{current_comment_id}" class="n S">◯</a></header>{commentParser(comments_forest[current_comment_id]['b'])}"""
        
        previous_comment_level = current_comment_level
        comment_counter += 1

    # JS managing scrolling features
    html_js = '<script>function checkKey(e){"38"==(e=e||window.event).keyCode?(e.preventDefault(),scrollToSibling("A")):"40"==e.keyCode?(e.preventDefault(),scrollToSibling("B")):"37"!=e.keyCode&&"80"!=e.keyCode||scrollToParent()}function scrollToSibling(e){var o,t=window.location.hash.substr(1),n=document.getElementById(t).getElementsByClassName(e)[0];n.classList.contains("D")||(o=n.getAttribute("href").substr(1),document.getElementById(o).scrollIntoView(!0),window.location.hash=o)}function scrollToParent(){var e=window.location.hash.substr(1);document.getElementById(e).parentNode.id.scrollIntoView(!0),window.location.hash=target_id}document.onkeydown=checkKey;</script>'

    # Merging this all together
    html_total = html_head+html_submission+html_firstpost+html_comments+html_js

    return html_total


def write_file(content, submission, now, output_directory):
    """
    Writes the HTML content into a file. Returns the filename
    """
    # keeping the submission name in URL
    sanitized_name = submission.permalink.split('/')[-2]

    # Reducing filename to 200 characters
    sanitized_name = (sanitized_name[:150]) if len(sanitized_name) > 150 else sanitized_name
    path = os.path.join(output_directory, f"{submission.subreddit.display_name}-{sanitized_name}-{now.strftime('%Y%m%d-%H%M%S')}.html")
    filename = f"{submission.subreddit.display_name}-{sanitized_name}-{now.strftime('%Y%m%d-%H%M%S')}.html"

    f = open(path, "wb")
    f.write(content.encode('utf-8'))
    f.close()

    return filename



# -------------------------- #
# Main function              #
# -------------------------- #

def main(submission_id, token, job_id, sort="confidence"):
    try:
        db = models.connect()
        models.start_job(db, job_id)

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.strftime(config["defaults"]["dateformat"])

        try:
            # "Connecting" to submission and getting information
            submission_api, nb_replies = connect_to_submission(submission_id, token)

            # Marking right now the number of comments in DB so we can calculate estimated remaining time
            models.write_nb_replies(db, job_id, nb_replies=nb_replies)
        
            # Getting the comment list and comment forest
            submission, comments_index, comments_forest = download_submission(submission_api, submission_id)
        except prawcore.exceptions.NotFound as e:
            log.error(f'{job_id}: prawcore.exceptions.NotFound ({e})')
            models.mark_job_failure(db, job_id, reason='SUBMISSION_NOT_FOUND')
            return
        except prawcore.exceptions.ResponseException as e:
            log.error(f'{job_id}: prawcore.exceptions.ResponseException ({e})', exc_info=True)
            models.mark_job_failure(db, job_id, reason='BAD_AUTHENTICATION')
            return
        else:
            log.info(f'{job_id}: submission downloaded')

        # Generating HTML structure
        while True: # allows to retry
            try:
                html = generate_html(submission, submission_id, now_str, None, comments_index, comments_forest)
            except RecursionError:
                if config["app"]["disable-recursion-limit"]:
                    sys.setrecursionlimit(sys.getrecursionlimit()*2)
                else:
                    log.error(f"The HTML structure could not be generated because the structure of the replies is going too deep for the program to handle. If you really want to handle such submissions, set the parameter \"disable-recursion-limit\" to true in the configuration. However, please note that this may lead to higher resource usage, and might potentially crash the app.")
                    models.mark_job_failure(db, job_id, reason='UNKNOWN')
                    return
            else:
                log.info(f'{job_id}: submission structured')
                break

        # Saving to disk
        try:
            filename = write_file(html, submission, now, config['paths']['output'])
        except PermissionError as e:
            log.error(f'{job_id}: PermissionError when writing the file ({e})')
            models.mark_job_failure(db, job_id, reason='BAD_PERMISSIONS')
            return
        except Exception as e:
            log.error(f'{job_id}: Uncaught exception when writing the file: {e}', exc_info=True)
            models.mark_job_failure(db, job_id, reason='UNKNOWN')
            return

        log.info(f'{job_id}: submission saved ({filename})')

        models.mark_job_success(db, job_id, filename=filename)
    except Exception as e:
        # general catch
        log.error(f'{job_id}: Uncaught exception: {e}', exc_info=True)
        models.mark_job_failure(db, job_id, reason='UNKNOWN')
        return
