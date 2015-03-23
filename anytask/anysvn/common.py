import os
import datetime
import StringIO
import re

import pysvn

from django.conf import settings

INDEX_RE = re.compile("^Index: (.*)")

def is_svn_exists(username, path=""):
    svn_full_path = os.path.join(settings.ANYSVN_REPOS_PATH, username, path)
    return os.path.exists(svn_full_path)

def get_svn_full_path(user, path=""):
    svn_full_path = os.path.join(settings.ANYSVN_REPOS_PATH, user.username, path)
    if not os.path.exists(svn_full_path):
        svn_full_path_lower = os.path.join(settings.ANYSVN_REPOS_PATH, user.username.lower(), path)
        if os.path.exists(svn_full_path_lower):
            return svn_full_path_lower
    return svn_full_path

def get_svn_uri(user, path=""):
    return "file://" + os.path.abspath(get_svn_full_path(user, path))

def get_svn_external_url(user, path=""):
    if is_svn_exists(user.username):
        return "http://anytask.urgu.org" + os.path.join(settings.ANYSVN_SVN_URL_PREFIX, user.username, path)
    elif is_svn_exists(user.username.lower()):
        return "http://anytask.urgu.org" + os.path.join(settings.ANYSVN_SVN_URL_PREFIX, user.username.lower(), path)

def svn_log(user, path=""):
    full_path = get_svn_uri(user, path)
    return pysvn.Client().log(full_path)

def svn_diff(user, rev_a, rev_b, path=""):
    path = path.lstrip("/")
    svn_uri = get_svn_uri(user)
    diff =  pysvn.Client().diff("/tmp/",
                           url_or_path=svn_uri,
                           header_encoding="UTF-8",
                           revision1=pysvn.Revision(pysvn.opt_revision_kind.number, rev_a),
                           revision2=pysvn.Revision(pysvn.opt_revision_kind.number, rev_b))

    if not path:
        return diff

    print_line = None
    diff_res = []
    for line in diff.split("\n"):
        m = INDEX_RE.search(line)
        if m:
            diff_path = m.group(1)
            if diff_path.startswith(path.encode("utf-8")):
                print_line = True
            else:
                print_line = False
        if print_line:
            diff_res.append(line)

    return "\n".join(diff_res)

def svn_log_rev_message(user, path=""):
    revisions = set()
    for log in svn_log(user, path):
        revisions.add(log["revision"].number)
        yield (log["revision"].number, log["author"], datetime.datetime.fromtimestamp(log["date"]), log["message"].strip())

    if path:
        first_revision = list(svn_log_rev_message(user))[-1]
        if first_revision[0] not in revisions:
            yield first_revision


def svn_log_head_revision(user, path=""):
    for log in svn_log_rev_message(user, path):
        return log[0]

def svn_log_min_revision(user, path=""):
    min_revision = None
    for log in svn_log_rev_message(user, path):
        if min_revision is None:
            min_revision = log[0]
            continue
        min_revision = min(min_revision, log[0])
    return min_revision
