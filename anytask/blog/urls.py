from django.conf.urls import patterns, url

urlpatterns = patterns(
    'blog.views',
    url(r'^$', 'blog_page'),
)
