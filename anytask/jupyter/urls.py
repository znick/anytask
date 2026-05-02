from django.urls import re_path
import jupyter.views

urlpatterns = [re_path(r'^assignments$', jupyter.views.update_jupyter_task, name="jupyter.views.update_jupyter_task"), ]
