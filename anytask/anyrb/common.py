import datetime

from django.conf import settings

from rbtools.api.client import RBClient

from anysvn.common import get_svn_uri

class AnyRB(object):
    def __init__(self):
        self.client = RBClient(settings.RB_API_URL, username=settings.RB_API_USERNAME, password=settings.RB_API_PASSWORD)

    def get_repository(self, user):
        username = user.username
        root = self.client.get_root()

        repo_count = root.get_repositories(counts_only=True).count
        repositories = root.get_repositories()

        repositories = root.get_repositories()
        try:
            while True:
                for repo in repositories:
                    if repo.fields["name"] == username:
                        return repo
                repositories = repositories.get_next()
        except StopIteration:
            return None

        return None

    def create_repository(self, user):
        root = self.client.get_root()
        root.get_repositories().create(name=user.username,
                                            path=get_svn_uri(user),
                                            tool="Subversion",
                                            public=False,
                                            access_users=",".join((user.username, settings.RB_API_USERNAME)),
                                            access_groups=settings.RB_API_DEFAULT_REVIEW_GROUP
                                            )
        return self.get_repository(user)

    def submit_review(self, user, diff_content, path="", summary="", description="", review_group_name=None, review_id=None): #review_id is for update
        descriptions = []
        if isinstance(summary, str):
            summary = summary.decode("utf-8")

        if isinstance(description, str):
            description = description.decode("utf-8")

        root = self.client.get_root()

        repository = self.get_repository(user)
        if repository is None:
            repository = self.create_repository(user)

        assert repository

        if review_id:
            review_request = root.get_review_request(review_request_id=review_id)
        else:
            review_request = root.get_review_requests().create(repository=repository.id, submit_as=user.username)

        try:
            review_request.get_diffs().upload_diff(diff_content, base_dir="/")
        except Exception:
            descriptions.append(u"WARNING: Diff has not been uploaded. Probably it contains non-ASCII filenames. Non-ASCII filenames are not supported.")


        descriptions.append(u"=== Added on {0} ===\n".format(datetime.datetime.now()))
        descriptions.append(description)

        draft = review_request.get_or_create_draft()
        description = u"\n".join(descriptions)
        draft.update(description=description, summary=summary)
        review_request.update(status="pending")

        if review_group_name:
            draft.update(target_groups=review_group_name)

        return review_request.id

    def get_review_url(self, request, review_id):
        host = request.get_host()
        proto = "http://"
        if request.is_secure():
            proto = "https://"

        return "{0}{1}/rb/r/{2}".format(proto, host, review_id)

