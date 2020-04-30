import admission.views
from django.conf.urls import url

urlpatterns = [
    url(r'^register$', admission.views.register,
        name="admission.views.register"),
    url(r'^activate/(?P<activation_key>\w+)/', admission.views.activate,
        name="admission.views.activate"),
    # url(r'^decline/(?P<activation_key>\w+)/', 'decline'),
]
