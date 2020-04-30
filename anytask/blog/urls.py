from django.conf.urls import url
import blog.views

urlpatterns = (
    url(r'^$', blog.views.blog_page, name='blog.views.blog_page'),
)
