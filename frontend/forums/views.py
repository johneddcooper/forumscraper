# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from forums.models import *
from django.shortcuts import render
import scraper.imaget as imaget
import os
import datetime
import glob
from django import forms

class search_form(forms.Form):
    text = forms.CharField()
    forum = forms.CharField()
    user = forms.CharField()
    start_date = forms.DateField()
    end_date = forms.DateField()
    

def search(request):
    if request.method == 'POST':
        form = search_form(request.POST)
        if form.is_valid():
             #process form data here
             print "in form data"
             search_text = form.cleaned_data['text']
             forum = form.cleaned_data['forum']
             user = form.cleaned_data['user']
             post_list = Posts.objects.filter(msg__icontains=search_text)

             if forum:
                 forum = Forums.objects.filter(name=forum)
                 if forum: post_list = post_list.filter()
             tmp = []
             for post in post_list:
                 image_list = Images.objects.filter(post_id=post.post_id)
                 image_src_list = []
                 for image in image_list:
                     image_src_list.append(get_image_path(image))
                 tmp.append((post, image_src_list))

             post_list = tmp
             print len(post_list)
             context = { 'form': form, 'post_list': post_list }
             return render(request, 'forums/results.html', context)
  
        else:
             form = search_form()
             context = { 'form': form }
    else:
             form = search_form()
             context = { 'form': form }
    return render(request, 'forums/search.html', context)


def get_image_path(image):
   try:

     image_dir = imaget.image_dir
     post = Posts.objects.get(post_id=image.post_id)
     if not post: return None
     print post.thread_id
     thread = Threads.objects.get(thread_id=post.thread_id)
     if not thread: return None

   except: return None

   image_path = os.path.join(image_dir,
       "threads",
       str(thread.thread_id))
   image_path = os.path.join(image_path, str(image.image_id) + ".*")
   image_path = glob.glob(image_path)
   

   if image_path: image_path = image_path[0]
   else: return None

   image_path = os.path.join("threads",
       str(thread.thread_id),
       image_path.split("/")[-1])

   print image_path

   return image_path

def index(request):
  forum_list = Forums.objects.order_by('forum_name')
  context = {'forum_list': forum_list}
  return render(request, 'forums/index.html', context)

def thread(request, thread_id, forum_id=0, subforum_id=0):
  post_list = Posts.objects.filter(thread_id=thread_id)
  thread = Threads.objects.get(thread_id=thread_id)
  last_thread_id = long(thread.thread_id) - 1
  next_thread_id = long(thread.thread_id) + 1
  tmp_list = []
  image_dir = "images"
  for post in post_list: 
    image_list = Images.objects.filter(post_id=post.post_id)
    image_src_list = []
    for image in image_list:
        image_src_list.append(get_image_path(image))
    tmp_list.append((post, image_src_list))
  post_list = tmp_list
  context = {'post_list': post_list, 'forum_id': forum_id, 'subforum_id': subforum_id, 'thread': thread, 'last_thread_id': last_thread_id, 'next_thread_id': next_thread_id}
  return render(request, 'forums/thread.html', context)

def subforum(request, subforum_id, forum_id=0):
  thread_list = Threads.objects.filter(subforum_id=subforum_id)

  forum = Forums.objects.filter(forum_id=forum_id)
  if forum: forum_name = forum[0].forum_name

  tmp = []
  for thread in thread_list:
      tmp.append((thread,len(Posts.objects.filter(thread_id=thread.thread_id))))
  thread_list = tmp
  thread_list.sort(key=lambda tup: tup[1])
  thread_list.reverse()
  context = {'thread_list': thread_list, 'forum_id': forum_id}
  return render(request, 'forums/subforum.html', context)

def forum(request, forum_id):
  subforum_list = Subforums.objects.filter(forum_id=forum_id)

  forum = Forums.objects.filter(forum_id=forum_id)
  if forum: forum_name = forum[0].forum_name

  print subforum_list
  tmp = []
  for sub in subforum_list:
      count = 0
      thread_list = Threads.objects.filter(subforum_id=sub.subforum_id)
      for thread in thread_list:
          if Posts.objects.filter(thread_id=thread.thread_id): count += 1
      tmp.append((sub, count))

  subforum_list = tmp
  subforum_list.sort(key=lambda tup: tup[1])
  subforum_list.reverse()
  context = {'subforum_list': subforum_list, 'forum_name': forum_name, 'forum_id': forum_id}
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
