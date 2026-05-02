import admission.views
from django.urls import re_path

urlpatterns = [
    re_path(r'^register$', admission.views.register,
        name="admission.views.register"),
    re_path(r'^activate/(?P<activation_key>\w+)/', admission.views.activate,
        name="admission.views.activate"),
    # re_path(r'^decline/(?P<activation_key>\w+)/', 'decline'),
]
