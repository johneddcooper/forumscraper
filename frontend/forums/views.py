# Create your views here.
from django.http import HttpResponse
from forums.models import *
from django.shortcuts import render
import scraper.imaget as imaget
import os

def get_image_path(image):
   image_dir = imaget.image_dir
   post = Posts.objects.get(post_id=image.post_id)
   if not post: return None
   thread = Threads.objects.get(thread_id=post.thread_id)
   if not thread: return None
   subforum = Subforums.objects.get(subforum_id=thread.subforum_id)
   if not subforum: return None
   forum = Forums.objects.get(forum_id=subforum.forum_id)
   if not forum: return None

   image_path = os.path.join(imaget.shellquotes(imaget.get_forum_name(forum.forum_url)),
       imaget.shellquotes(subforum.subforum_name),
       imaget.shellquotes(thread.thread_name))
   image_path = os.path.join(image_path, str(image.image_id) + ".jpg")

   return image_path

def index(request):
  forum_list = Forums.objects.order_by('forum_name')
  context = {'forum_list': forum_list}
  return render(request, 'forums/index.html', context)

def thread(request, thread_id, forum_id=0, subforum_id=0):
  post_list = Posts.objects.filter(thread_id=thread_id)
  thread = Threads.objects.get(thread_id=thread_id)
  tmp_list = []
  image_dir = "images"
  for post in post_list: 
    image_list = Images.objects.filter(post_id=post.post_id)
    image_src_list = []
    for image in image_list:
        image_src_list.append(get_image_path(image))
    tmp_list.append((post, image_src_list))
  post_list = tmp_list
  context = {'post_list': post_list, 'forum_id': forum_id, 'subforum_id': subforum_id, 'thread': thread}
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
  U = Users.objects.filter(user_id=user_id)
  if U: 
    U = U[0]
  else:
    context = {'user': False}
    return render(request, 'forums/user.html', context)
  last_u_id = long(user_id) - 1
  next_u_id = long(user_id) + 1
  print "User signature: "
  print U.sig
  #U.sig.replace('\"', '"')
  #U.sig.replace('\\n', '')
  print "User signature: "
  print U.sig
  tmp_list = []
  post_list = Posts.objects.filter(user_id=user_id)
  if post_list: print "post list found:"
  print post_list
  for post in post_list: 
    image_list = Images.objects.filter(post_id=post.post_id)
    image_src_list = []
    for image in image_list:
        image_src_list.append(get_image_path(image))
    tmp_list.append((post, image_src_list))
  post_list = tmp_list
  forum = Forums.objects.filter(forum_id=U.forum_id)[0]
  context = {'user': U, 'forum': forum, 'post_list': post_list, 'last_u_id': last_u_id, 'next_u_id': next_u_id, 'user_page': True}
  return render(request, 'forums/user.html', context)

def post(request, post_id):
  post = Posts.objects.filter(post_id=post_id)
  post = str(post[0]).replace('\\n', '')
  print post
  return HttpResponse("You're looking at the results of \n\n\n %s." % post)
