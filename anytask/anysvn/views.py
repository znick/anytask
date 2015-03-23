import base64
import os
import shutil

from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import View

from courses.models import Course

class HttpResponseUnauthorized(HttpResponse):
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)
        self.status_code = 401
        self["WWW-Authenticate"] = 'Basic realm="AnyTask SVN access"'

class SvnAccesss(View):

    def _get_user(self, username, password):
        return authenticate(username=username, password=password)

    def create_svn(self, svn_path):
        svn_full_path = os.path.join(settings.ANYSVN_REPOS_PATH, svn_path)
        refference_svn_full_path = os.path.join(settings.ANYSVN_REPOS_PATH, settings.ANYSVN_REFFERENCE_REPO)
        shutil.copytree(refference_svn_full_path, svn_full_path, symlinks=True)

    def ensure_svn_exists(self, svn_path):
        svn_full_path = os.path.join(settings.ANYSVN_REPOS_PATH, svn_path)
        if not os.path.exists(svn_full_path):
            self.create_svn(svn_path)

    def check_svn_access(self, svn_path, username, password):
        user = self._get_user(username, password)
        if not (user and user.is_active):
            return False

        if svn_path == username:
            return True

        for course in Course.objects.all():
            if course.user_is_teacher(user):
                return True
        return False

    def check_svn_access_and_ensure_exists(self, svn_path, username, password):
        if not self.check_svn_access(svn_path, username, password):
            return False
        self.ensure_svn_exists(svn_path)
        return True

    def dispatch(self, request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth_str = request.META['HTTP_AUTHORIZATION']
            auth_str_parts = auth_str.split()

            if auth_str_parts[0] != "Basic":
                return HttpResponseForbidden()

            username, password = base64.b64decode(auth_str_parts[1]).split(":", 1)
            svn_url = request.META.get('HTTP_REFERER', '')

            if not svn_url.startswith(settings.ANYSVN_SVN_URL_PREFIX):
                return HttpResponse()
                return HttpResponseUnauthorized()

            svn_path = svn_url[len(settings.ANYSVN_SVN_URL_PREFIX):]
            if svn_path and "/" in svn_path:
                svn_path = svn_path.split("/")[0]

            if self.check_svn_access_and_ensure_exists(svn_path, username, password):
                return HttpResponse()

        return HttpResponseUnauthorized()
