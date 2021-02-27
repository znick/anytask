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

from django.conf.urls import *
from django.views.generic.base import TemplateView

from registration.backends.default_with_names import AnytaskLoginForm, \
    AnytaskPasswordResetForm, AnytaskSetPasswordForm, \
    AnytaskPasswordChangeForm, BootStrapRegistrationFormWithNames
from .views import ActivationView
from .views import RegistrationView
from .views import ajax_check_username, ajax_check_email
from django.urls import reverse_lazy

from django.contrib.auth import views as auth_views

urlpatterns = [url(r'^activate/complete/$',
                   TemplateView.as_view(
                       template_name='registration/activation_complete.html'),
                   name='registration_activation_complete'),
               # Activation keys get matched by \w+ instead of the more specific
               # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
               # that way it can return a sensible "invalid key" message instead of a
               # confusing 404.
               url(r'^activate/(?P<activation_key>\w+)/$',
                   ActivationView.as_view(),
                   {
                       'backend': 'registration.backends.default_with_names.DefaultBackend'},
                   name='registration_activate'),
               url(r'^register/$',
                   RegistrationView.as_view(form_class=BootStrapRegistrationFormWithNames),
                   {
                       'backend': 'registration.backends.default_with_names.DefaultBackend'},
                   name='registration_register'),
               url(r'^register/complete/$',
                   TemplateView.as_view(
                       template_name='registration/registration_complete.html'),
                   name='registration_complete'),
               url(r'^register/closed/$',
                   TemplateView.as_view(
                       template_name='registration/registration_closed.html'),
                   name='registration_disallowed'),
               url(r'^register/ajax_check_username/$',
                   ajax_check_username,
                   name='registration.views.ajax_check_username'),
               url(r'^register/ajax_check_email/$',
                   ajax_check_email,
                   name='registration.views.ajax_check_email'),
               url(r'^login/$',
                   auth_views.LoginView.as_view(template_name='registration/login.html', form_class=AnytaskLoginForm),
                   name='auth_login'),
               url(r'^password/reset/$', auth_views.PasswordResetView.as_view(
                   success_url=reverse_lazy('auth_password_reset_done'),
                   form_class=AnytaskPasswordResetForm),
                   name='auth_password_reset'),
               url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
                   auth_views.PasswordResetConfirmView.as_view(
                       success_url=reverse_lazy('auth_password_reset_complete'),
                       form_class=AnytaskSetPasswordForm),
                   name='auth_password_reset_confirm'),
               url(r'^password/change/$',
                   auth_views.PasswordChangeView.as_view(
                       success_url=reverse_lazy('auth_password_change_done'),
                       form_class=AnytaskPasswordChangeForm),
                   name='auth_password_change'),
               url(r'', include('registration.auth_urls')),
]
