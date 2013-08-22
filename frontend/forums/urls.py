from django.conf.urls import patterns, url

from forums import views

urlpatterns = patterns('',
    # ex: /forums/
    url(r'^$', views.index),
    url(r'^posts/(?P<post_id>\d+)/$', views.post),
    url(r'^posts/(?P<post_id>\d+)/$', views.post),
    url(r'^search/$', views.search),
    url(r'^results/$', views.search),
    url(r'^threads/(?P<thread_id>\d+)/$', views.thread),
    # ex: /forums/5/
    url(r'^(?P<forum_id>\d+)/(?P<subforum_id>\d+)/(?P<thread_id>\d+)/$', views.thread),
    url(r'^(?P<forum_id>\d+)/(?P<subforum_id>\d+)/$', views.subforum),
    url(r'^(?P<forum_id>\d+)/$', views.forum),
    url(r'^users/(?P<user_id>\d+)/$', views.user),
)
