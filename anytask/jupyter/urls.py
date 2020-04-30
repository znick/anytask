from django.conf.urls import url
import jupyter.views

urlpatterns = [url(r'^assignments$', jupyter.views.update_jupyter_task), ]
