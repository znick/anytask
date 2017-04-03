"""
URLconf for registration and activation, using django-registration's
default backend.

If the default behavior of these views is acceptable to you, simply
use a line like this in your root URLconf to set up the default URLs
for registration::

    (r'^accounts/', include('registration.backends.default.urls')),

This will also automatically set up the views in
``django.contrib.auth`` at sensible default locations.

If you'd like to customize the behavior (e.g., by passing extra
arguments to the various views) or split up the URLs, feel free to set
up your own URL patterns for these views instead.

"""


from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from registration.backends.default_with_names import AnytaskLoginForm, AnytaskPasswordResetForm, AnytaskSetPasswordForm, AnytaskPasswordChangeForm
from registration.views import activate
from registration.views import register
from registration.views import ajax_check_username, ajax_check_email

from django.contrib.auth import views as auth_views

urlpatterns = patterns('',
                       url(r'^activate/complete/$',
                           direct_to_template,
                           {'template': 'registration/activation_complete.html'},
                           name='registration_activation_complete'),
                       # Activation keys get matched by \w+ instead of the more specific
                       # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
                       # that way it can return a sensible "invalid key" message instead of a
                       # confusing 404.
                       url(r'^activate/(?P<activation_key>\w+)/$',
                           activate,
                           {'backend': 'registration.backends.default_with_names.DefaultBackend'},
                           name='registration_activate'),
                       # url(r'^register/$',
                       #     register,
                       #     {'backend': 'registration.backends.default_with_names.DefaultBackend'},
                       #     name='registration_register'),
                       url(r'^register/complete/$',
                           direct_to_template,
                           {'template': 'registration/registration_complete.html'},
                           name='registration_complete'),
                       url(r'^register/closed/$',
                           direct_to_template,
                           {'template': 'registration/registration_closed.html'},
                           name='registration_disallowed'),
                       url(r'^register/ajax_check_username/$',
                           ajax_check_username),
                       url(r'^register/ajax_check_email/$',
                           ajax_check_email),
                       url(r'^login/$',
                           auth_views.login,
                           {'template_name': 'registration/login.html', 'authentication_form' : AnytaskLoginForm},
                           name='auth_login'),
                       # url(r'^password/reset/$',
                       #     auth_views.password_reset,
                       #     {'password_reset_form': AnytaskPasswordResetForm},
                       #     name='auth_password_reset'),
                       url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           auth_views.password_reset_confirm,
                           {'set_password_form': AnytaskSetPasswordForm},
                           name='auth_password_reset_confirm'),
                       # url(r'^password/change/$',
                       #     auth_views.password_change,
                       #     {'password_change_form': AnytaskPasswordChangeForm},
                       #     name='auth_password_change'),
                       (r'', include('registration.auth_urls')),
                       )
