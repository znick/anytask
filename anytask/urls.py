from django.urls import re_path, include
from django.conf import settings
from django.views.generic.base import TemplateView
import users.views
import django.contrib.auth.views
import django.views.static
import index.views
import admission.views

from middleware.lang_middleware import set_lang_view, get_lang_view

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^course/', include('courses.urls')),
    re_path(r'^issue/', include('issues.urls')),
    re_path(r'^school/', include('schools.urls')),
    re_path(r'^task/', include('tasks.urls')),
    re_path(r'^user/', include('users.urls')),
    re_path(r'^users/(?P<username>.*)/', users.views.users_redirect),
    re_path(r'^setlanguage/', users.views.set_user_language),
    re_path(r'^invites/', include('invites.urls')),
    re_path(r'^anyrb/', include('anyrb.urls')),
    re_path(r'^accounts/logout/$', django.contrib.auth.views.LogoutView.as_view(next_page='/'), name='logout'),
    re_path(r'^accounts/profile/(?P<username>.*)/(?P<year>\d+)', users.views.profile, name='users.views.profile'),
    re_path(r'^accounts/profile/(?P<username>.*)', users.views.profile, name='users.views.profile'),
    re_path(r'^accounts/profile', users.views.profile, name='users.views.profile'),
    re_path(r'^accounts/', include('registration.backends.default_with_names.urls')),
    re_path(r'^static/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^about$', TemplateView.as_view(template_name='about.html')),
    re_path(r'^$', index.views.index, name="index.views.index"),
    re_path(r'^archive/', index.views.archive_index, name="index.views.archive_index"),
    re_path(r'^search/', include('search.urls')),
    re_path(r'^staff', include('staff.urls')),
    re_path(r'^mail/', include('mail.urls')),
    re_path(r'^admission/', include('admission.urls')),
    re_path(r'^shad2017/register', admission.views.register),
    re_path(r'^shad2017/activate/(?P<activation_key>\w+)/', admission.views.activate),
    re_path(r'^shad2017/decline/(?P<activation_key>\w+)/', admission.views.decline),
    re_path(r'^lesson/', include('lessons.urls')),
    re_path(r'^api/', include('api.urls')),
    re_path(r'^jupyter/', include('jupyter.urls')),
    re_path(r'^set_lang/', set_lang_view, name='set_lang'),
    re_path(r'^get_lang/', get_lang_view, name='get_lang'),
    re_path(r'^robots.txt$', index.views.robotstxt_view, name="index.views.robotstxt_view"),
]
