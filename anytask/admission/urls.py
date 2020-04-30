from django.conf.urls import patterns, url
import admission.views

urlpatterns = [
    url(r'^register$', admission.views.register),
    url(r'^activate/(?P<activation_key>\w+)/', admission.views.activate),
    # url(r'^decline/(?P<activation_key>\w+)/', 'decline'),
]
