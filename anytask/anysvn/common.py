import os
import datetime
import re
from svn import SvnLog, SvnDiff

from django.conf import settings

def is_svn_exists(username, path=""):
    svn_full_path = os.path.join(settings.ANYSVN_REPOS_PATH, username.lower(), path)
    return os.path.exists(svn_full_path)

def get_svn_full_path(user, path=""):
    svn_full_path_lower = os.path.join(settings.ANYSVN_REPOS_PATH, user.username.lower(), path)
    return svn_full_path_lower

def get_svn_uri(user, path=""):
    return "file://" + os.path.abspath(get_svn_full_path(user, path))

def get_svn_external_url(user, path=""):
    return "http://anytask.urgu.org" + os.path.join(settings.ANYSVN_SVN_URL_PREFIX, user.username.lower(), path)

def svn_log(user, path=""):
    full_path = get_svn_uri(user, path)
    return SvnLog(full_path).get_logs()

def svn_diff(user, rev_a=0, rev_b="HEAD", path=""):
    path = path.lstrip("/")
    svn_uri = get_svn_uri(user)
    diff = SvnDiff(svn_uri, path, rev_a, rev_b, max_diff_size = settings.ANYSVN_MAX_DIFF_SIZE).get_diff()
    diff = "\n".join(diff)
    return diff

def svn_log_rev_message(user, path=""):
    revisions = set()
    for log in svn_log(user, path):
        revisions.add(log["revision"])
        yield (log["revision"], log["author"], log["datetime"], log["message"].strip())

