"""
URL patterns for the views included in ``django.contrib.auth``.

Including these URLs (via the ``include()`` directive) will set up the
following patterns based at whatever URL prefix they are included
under:

* User login at ``login/``.

* User logout at ``logout/``.

* The two-step password change at ``password/change/`` and
  ``password/change/done/``.

* The four-step password reset at ``password/reset/``,
  ``password/reset/confirm/``, ``password/reset/complete/`` and
  ``password/reset/done/``.

The default registration backend already has an ``include()`` for
these URLs, so under the default setup it is not necessary to manually
include these views. Other backends may or may not include them;
consult a specific backend's documentation for details.

"""
from django.urls import re_path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
    # re_path(r'^login/$',
    #     auth_views.LoginView.as_view(
    #         template_name='registration/login.html'),
    #     name='auth_login'),
    re_path(r'^logout/$',
        auth_views.LogoutView.as_view(
            template_name='registration/logout.html'),
        name='auth_logout'),
    # re_path(r'^password/change/$',
    #     auth_views.PasswordChangeView.as_view(
    #         success_url=reverse_lazy('auth_password_change_done')),
    #     name='auth_password_change'),
    re_path(r'^password/change/done/$',
        auth_views.PasswordChangeDoneView.as_view(),
        name='auth_password_change_done'),
    # re_path(r'^password/reset/$',
    #     auth_views.PasswordResetView.as_view(
    #         success_url=reverse_lazy('auth_password_reset_done')),
    #     name='auth_password_reset'),
    re_path(r'^password/reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(),
        name='auth_password_reset_complete'),
    re_path(r'^password/reset/done/$',
        auth_views.PasswordResetDoneView.as_view(),
        name='auth_password_reset_done'),
    # re_path(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
    #     auth_views.PasswordResetConfirmView.as_view(
    #         success_url=reverse_lazy('auth_password_reset_complete')),
    #     name='auth_password_reset_confirm'),
]
