# -*- coding: utf-8 -*-
import datetime
import os
import requests

from django.conf import settings

from rbtools.api.client import RBClient

# from anysvn.common import get_svn_uri, svn_diff


class AnyRB(object):
    def __init__(self, event):
        self.client = RBClient(settings.RB_API_URL, username=settings.RB_API_USERNAME, password=settings.RB_API_PASSWORD)
        self.event = event

    def upload_review(self):
        if len(self.event.file_set.all()) == 0:
            return

        files_diff = []
        empty = True
        import magic
        for f in self.event.file_set.all():
            mime_type = magic.from_buffer(f.file.read(1024), mime=True)
            if mime_type[:4] != 'text':
                continue

            empty = False
            file_content = []
            for line in f.file:
                file_content.append(line.decode('utf-8'))

            from difflib import unified_diff
            fname = f.filename()
            from_name = u'a/{0}'.format(fname)
            to_name = u'b/{0}'.format(fname)

            diff = [(u'diff --git {0} {1}'.format(from_name, to_name))]
            from_name = u'/dev/null'

            diff_content = unified_diff('',
                                        file_content,
                                        fromfile=from_name,
                                        tofile=to_name.encode('utf-8'))
            for line in diff_content:
                line = line.strip()
                if isinstance(line, str):
                    diff.append(line.decode('utf-8'))
                else:
                    diff.append(line)

            files_diff.append(u'\n'.join(diff))

        files_diff = u'\n'.join(files_diff)

        if empty:
            return

        review_request = self.get_or_create_review_request()
        review_request.get_diffs().upload_diff(files_diff.encode('utf-8'))

        draft = review_request.get_or_create_draft()
        issue = self.event.issue
        summary = u'[{0}][{1}] {2}'.format(issue.student.get_full_name(), 
                                          issue.task.group,
                                          issue.task.title)
        description = u'{0}'.format(
            issue.get_absolute_url(),
        )

        draft = draft.update(summary=summary,
                             description=description.encode('utf-8'),
                             target_people='anytask', public=True,
                             )
        pass

    def get_or_create_review_request(self):
        root = self.client.get_root()

        review_request = None
        try:
            review_id = self.event.issue.get_byname('review_id')
            review_request = root.get_review_request(review_request_id=review_id)
        except Exception, e:
            repository_name = str(self.event.issue.id)
            os.symlink(settings.RB_SYMLINK_DIR,settings.RB_SYMLINK_DIR+repository_name)
            repository = root.get_repositories().create(
                     name=repository_name,
                     path=settings.RB_SYMLINK_DIR+repository_name+'/.git',
                     tool='Git',
                     public=False)
            root.get_repository(repository_id=repository.id).update(grant_type='add', 
                                                      grant_entity='user',
                                                      grant_name=self.event.author)
            root.get_repository(repository_id=repository.id).update(grant_type='add',
                                                      grant_entity='group',
                                                      grant_name='teachers')
            review_request = root.get_review_requests().create(repository=repository.id)
        self.event.issue.set_byname('review_id', review_request.id, self.event.author)
        return review_request


    # def get_repository(self, user):
        # username = user.username
        # root = self.client.get_root()
        # for repo in root.get_repositories():
            # if repo.fields["name"] == username:
                # return repo

        # return None

    # def create_repository(self, user):
        # root = self.client.get_root()
        # root.get_repositories().create(name=user.username,
                                            # path=get_svn_uri(user),
                                            # tool="Subversion",
                                            # public=False,
                                            # access_users=",".join((user.username, settings.RB_API_USERNAME)),
                                            # access_groups=settings.RB_API_DEFAULT_REVIEW_GROUP
                                            # )
        # return self.get_repository(user)

    # def submit_review(self, user, rev_a, rev_b, path="", summary="", description="",review_group_name=None):
        # if isinstance(summary, unicode):
            # summary = summary.encode("utf-8")

        # root = self.client.get_root()

        # repository = self.get_repository(user)
        # if repository is None:
            # repository = self.create_repository(user)

        # review_request = root.get_review_requests().create(repository=repository.id, submit_as=user.username)

        # diff_content = svn_diff(user, rev_a, rev_b, path=path)
        # try:
            # review_request.get_diffs().upload_diff(diff_content, base_dir="/")
        # except Exception:
            # description +="\n WARNING: Diff has not been uploaded. Probably it contains non-ASCII filenames. Non-ASCII filenames are not supported."


        # draft = review_request.get_or_create_draft()
        # description = "=== Added on {0} ===\n".format(datetime.datetime.now()) + description
        # draft = draft.update(summary=summary, description=description)

        # if review_group_name:
            # draft.update(target_groups=review_group_name)

        # return review_request.id

    # def update_review(self, user, rev_a, rev_b, review_id, description="", path=""):
        # root = self.client.get_root()

        # review_request = root.get_review_request(review_request_id=review_id)

        # descriptions = [review_request.description.encode("utf-8")]
        # descriptions.append("=== Added on {0} ===".format(datetime.datetime.now()))
        # descriptions.append(description)

        # draft = review_request.get_or_create_draft()

        # diff_content = svn_diff(user, rev_a, rev_b, path=path)
        # try:
            # review_request.get_diffs().upload_diff(diff_content, base_dir="/")
        # except Exception:
            # descriptions.append("\n WARNING: Diff has not been uploaded. Probably it contains non-ASCII filenames. Non-ASCII filenames are not supported.")
        # draft.update(description="\n".join(descriptions))
        # review_request.update(status="pending")

        # return review_id


    # def get_review_url(self, request, review_id):
        # host = request.get_host()
        # proto = "http://"
        # if request.is_secure():
            # proto = "https://"

        # return "{0}{1}/rb/r/{2}".format(proto, host, review_id)

def update_status_review_request(review_id, status):
    url = settings.RB_API_URL + '/api/review-requests/' + review_id +'/'
    req = requests.put(url,data={'status': status},
                       auth=(settings.RB_API_USERNAME, settings.RB_API_PASSWORD))