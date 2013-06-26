# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models

class Forums(models.Model):
    forum_id = models.IntegerField(primary_key=True)
    forum_name = models.CharField(max_length=50L, blank=True)
    forum_url = models.CharField(max_length=50L, blank=True)
    class Meta:
        db_table = 'FORUMS'

class Images(models.Model):
    image_id = models.IntegerField(primary_key=True)
    thread_id = models.IntegerField(null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    post_id = models.IntegerField(null=True, blank=True)
    image_src = models.CharField(max_length=200L, blank=True)
    class Meta:
        db_table = 'IMAGES'

class Posts(models.Model):
    post_id = models.IntegerField(primary_key=True)
    postdate = models.CharField(max_length=50L, blank=True)
    postlink = models.CharField(max_length=50L, blank=True)
    msg = models.TextField(blank=True)
    edits = models.CharField(max_length=1000L, blank=True)
    thread_id = models.IntegerField(null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = 'POSTS'
    def __unicode__(self):
        return self.postdate + "\n" + self.msg

class Subforums(models.Model):
    subforum_id = models.IntegerField(primary_key=True)
    subforum_name = models.CharField(max_length=50L, blank=True)
    subforum_url = models.CharField(max_length=50L, blank=True)
    forum_id = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = 'SUBFORUMS'

class Threads(models.Model):
    thread_id = models.IntegerField(primary_key=True)
    thread_name = models.CharField(max_length=100L, blank=True)
    subforum_id = models.IntegerField(null=True, blank=True)
    subforum_page = models.CharField(max_length=50L, blank=True)
    class Meta:
        db_table = 'THREADS'

class Users(models.Model):
    user_id = models.IntegerField(primary_key=True)
    forum_id = models.IntegerField(null=True, blank=True)
    username = models.CharField(max_length=50L, blank=True)
    usertitle = models.CharField(max_length=50L, blank=True)
    joindate = models.CharField(max_length=50L, blank=True)
    sig = models.CharField(max_length=10000L, blank=True)
    class Meta:
        db_table = 'USERS'

