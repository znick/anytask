# -*- coding: utf-8 -*-
import logging
import os
import requests

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _

from rbtools.api.client import RBClient
from .unpacker import unpack_files

logger = logging.getLogger('django.request')


class AnyRB(object):
    def __init__(self, event):
        self.client = RBClient(settings.RB_API_URL, username=settings.RB_API_USERNAME,
                               password=settings.RB_API_PASSWORD)
        self.event = event

    def upload_review(self):
        if len(self.event.file_set.all()) == 0:
            return None

        files_diff = []
        empty = True
        import magic

        with unpack_files(self.event.file_set.all()) as files:
            for f in files:
                mime_type = magic.from_buffer(f.file.read(1024), mime=True)
                if mime_type[:4] != 'text':
                    continue

                empty = False
                file_content = []
                for line in f.file:
                    try:
                        file_content.append(line.decode('utf-8'))
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        file_content.append(line.decode('cp1251'))

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
                return None

            review_request = self.get_review_request()
            if review_request is None:
                review_request = self.create_review_request()
            if review_request is None:
                return review_request

            logger.info("Diff to upload: >>>%s<<<", files_diff)
            review_request.get_diffs().upload_diff(files_diff.encode('utf-8'))

            draft = review_request.get_or_create_draft()
            issue = self.event.issue
            task_title = issue.task.get_title(issue.student.profile.language)
            summary = u'[{0}][{1}] {2}'.format(issue.student.get_full_name(),
                                               issue.task.course.get_user_group(issue.student),
                                               task_title)

            description_template = \
                _(u'zadacha') + ': "{0}", ' + \
                _(u'kurs') + ': [{1}]({2}{3})\n' + \
                _(u'student') + ': [{4}]({2}{5})\n' + '[' + \
                _(u'obsuzhdenie_zadachi') + ']({2}{6})'

            description = description_template.format(
                task_title,
                issue.task.course,
                Site.objects.get_current().domain,
                issue.task.course.get_absolute_url(),
                issue.student.get_full_name(),
                issue.student.get_absolute_url(),
                issue.get_absolute_url()
            )

            draft = draft.update(summary=summary,
                                 description=description,
                                 description_text_type='markdown',
                                 target=settings.RB_API_USERNAME, public=True,
                                 )
            return review_request.id

    # def get_or_create_review_request(self):
    #     root = self.client.get_root()

    #     review_request = None
    #     try:
    #         review_id = self.event.issue.get_byname('review_id')
    #         review_request = root.get_review_request(review_request_id=review_id)
    #     except (AttributeError, ValueError):
    #         course_id = self.event.issue.task.course.id
    #         repository_name = str(self.event.issue.id)
    #         os.symlink(settings.RB_SYMLINK_DIR,os.path.join(settings.RB_SYMLINK_DIR, repository_name))
    #         repository = root.get_repositories().create(
    #                  name=repository_name,
    #                  path=settings.RB_SYMLINK_DIR+repository_name+'/.git',
    #                  tool='Git',
    #                  public=False)
    #         root.get_repository(repository_id=repository.id).update(grant_type='add',
    #                                                   grant_entity='user',
    #                                                   grant_name=self.event.author)
    #         root.get_repository(repository_id=repository.id).update(grant_type='add',
    #                                                   grant_entity='group',
    #                                                   grant_name='teachers')
    #         root.get_repository(repository_id=repository.id).update(grant_type='add',
    #                                                   grant_entity='group',
    #                                                   grant_name='teachers_{0}'.format(course_id))

    #         review_request = root.get_review_requests().create(repository=repository.id)
    #     self.event.issue.set_byname('review_id', review_request.id, self.event.author)
    #     return review_request

    def get_review_request(self):
        root = self.client.get_root()

        review_request = None
        try:
            review_id = self.event.issue.get_byname('review_id')
        except (AttributeError, ValueError):
            logger.info("Issue '%s' has not review_id.", self.event.issue.id)
            return None
        try:
            review_request = root.get_review_request(review_request_id=review_id)
            return review_request
        except Exception as e:
            logger.info("Issue '%s' has not RB review_request. Exception: '%s'.", self.event.issue.id, e)
            return None

    def create_review_request(self):
        root = self.client.get_root()

        review_request = None
        course_id = self.event.issue.task.course.id
        repository_name = str(self.event.issue.id)
        repository_path = os.path.join(settings.RB_SYMLINK_DIR, repository_name)
        if not os.path.exists(repository_path):
            os.symlink(settings.RB_SYMLINK_DIR, repository_path)

        try:

            repository = None
            try:
                repository = root.get_repositories().create(
                    name=repository_name,
                    path=os.path.join(repository_path, '.git'),
                    tool='Git',
                    public=False)
            except Exception:
                logger.warning("Cant create repository '%s', trying to find it", repository_name)
                repository = self.get_repository(repository_name)

            if repository is None:
                raise Exception("Cant find repository '%s', trying to find it", repository_name)

            root.get_repository(repository_id=repository.id).update(grant_type='add',
                                                                    grant_entity='user',
                                                                    grant_name=self.event.issue.student)
            root.get_repository(repository_id=repository.id).update(grant_type='add',
                                                                    grant_entity='group',
                                                                    grant_name='teachers_{0}'.format(course_id))

            review_request = root.get_review_requests().create(repository=repository.id)
            self.event.issue.set_byname('review_id', review_request.id, self.event.author)
        except Exception as e:
            logger.exception("Exception while creating review_request. Exception: '%s'. Issue: '%s'", e,
                             self.event.issue.id)
            return None

        return review_request

    def get_repository(self, name):
        root = self.client.get_root()

        repositories = root.get_repositories()
        try:
            while True:
                for repo in repositories:
                    if repo.name == name:
                        return repo
                repositories = repositories.get_next()
        except StopIteration:
            return None

        return None


class RbReviewGroup(object):
    def __init__(self, review_group_name):
        self.review_group_name = review_group_name

    def create(self):
        url = settings.RB_API_URL + "/api/groups/"
        payload = {
            'display_name': self.review_group_name,
            'invite_only': True,
            'name': self.review_group_name,
        }
        r = requests.post(url, auth=(settings.RB_API_USERNAME, settings.RB_API_PASSWORD), data=payload)
        logger.info("RevewBoard create for '%s' : '%s' : '%s'", self.review_group_name, r.status_code, r.content)
        assert r.status_code in (200, 201, 223, 409)

    def list(self):
        url = settings.RB_API_URL + "/api/groups/{0}/users/".format(self.review_group_name)
        r = requests.get(url, auth=(settings.RB_API_USERNAME, settings.RB_API_PASSWORD))
        logger.info("RevewBoard list for '%s' : '%s'", self.review_group_name, r.content)
        for user in r.json()["users"]:
            yield user["username"]

    def user_add(self, username):
        url = settings.RB_API_URL + "/api/groups/{0}/users/".format(self.review_group_name)
        payload = {
            'username': username,
        }
        r = requests.post(url, auth=(settings.RB_API_USERNAME, settings.RB_API_PASSWORD), data=payload)
        logger.info("ReviewGroup user_add Add '%s' to '%s. Status:'%s'",
                    username, self.review_group_name, r.status_code)
        assert r.status_code in (200, 201, 204)

    def user_del(self, username):
        url = settings.RB_API_URL + "/api/groups/{0}/users/{1}/".format(self.review_group_name, username)
        r = requests.delete(url, auth=(settings.RB_API_USERNAME, settings.RB_API_PASSWORD))
        logger.info("ReviewGroup user_del Drop '%s' from '%s'. Status:'%s'",
                    username, self.review_group_name, r.status_code)
        assert r.status_code in (200, 201, 204)

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
        # description +="\n WARNING: Diff has not been uploaded. Probably it contains non-ASCII filenames.
        # Non-ASCII filenames are not supported."

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
        # descriptions.append("\n WARNING: Diff has not been uploaded. Probably it contains non-ASCII filenames.
        # Non-ASCII filenames are not supported.")
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
    url = settings.RB_API_URL + '/api/review-requests/' + review_id + '/'
    requests.put(url, data={'status': status}, auth=(settings.RB_API_USERNAME, settings.RB_API_PASSWORD))
