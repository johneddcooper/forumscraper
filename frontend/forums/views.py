# Create your views here.
from django.http import HttpResponse
from forums.models import *
from django.shortcuts import render

def index(request):
  forum_list = Forums.objects.order_by('forum_name')
  context = {'forum_list': forum_list}
  return render(request, 'forums/index.html', context)

def thread(request, thread_id, forum_id=0, subforum_id=0):
  post_list = Posts.objects.filter(thread_id=thread_id)
  context = {'post_list': post_list, 'forum_id': forum_id, 'subforum_id': subforum_id}
  return render(request, 'forums/thread.html', context)

def subforum(request, subforum_id, forum_id=0):
  thread_list = Threads.objects.filter(subforum_id=subforum_id)
  context = {'thread_list': thread_list, 'forum_id': forum_id}
  return render(request, 'forums/subforum.html', context)

def forum(request, forum_id):
  subforum_list = Subforums.objects.filter(forum_id=forum_id)
  print subforum_list
  context = {'subforum_list': subforum_list}
  return render(request, 'forums/forum.html', context)

def user(request, user_id):
  U = Users.objects.filter(user_id=user_id)[0]
  print "User signature: "
  print U.sig
  post_list = Posts.objects.filter(user_id=user_id)
  forum = Forums.objects.filter(forum_id=U.forum_id)[0]
  context = {'user': U, 'forum': forum, 'post_list': post_list}
  return render(request, 'forums/user.html', context)

def post(request, post_id):
  post = Posts.objects.filter(post_id=post_id)
  post = str(post[0]).replace('\\n', '')
  print post
  return HttpResponse("You're looking at the results of \n\n\n %s." % post)
