from django.conf.urls import patterns, url

from forums import views

urlpatterns = patterns('',
    # ex: /forums/
    url(r'^$', views.index, name='index'),
    url(r'^posts/(?P<post_id>\d+)/$', views.post, name='detail'),
    url(r'^posts/(?P<post_id>\d+)/$', views.post, name='detail'),
    url(r'^search/$', views.search, name='detail'),
    url(r'^results/$', views.search, name='detail'),
    url(r'^threads/(?P<thread_id>\d+)/$', views.thread, name='detail'),
    # ex: /forums/5/
    url(r'^(?P<forum_id>\d+)/(?P<subforum_id>\d+)/(?P<thread_id>\d+)/$', views.thread, name='detail'),
    url(r'^(?P<forum_id>\d+)/(?P<subforum_id>\d+)/$', views.subforum, name='detail'),
    url(r'^(?P<forum_id>\d+)/$', views.forum, name='detail'),
    url(r'^users/(?P<user_id>\d+)/$', views.user, name='detail'),
)
