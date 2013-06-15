import MySQLdb as mdb
import sys
from local_settings import *
import re

class post:

  def __init__(self, home, subname, sublink, subpage, thread, date, plink, msg, name, title, joindate, ulink, sig, edit):

    self.home = home
    self.subname = subname
    self.thread = thread
#temp_date = re.search(r'\d+?[a-zA-Z]{2} [a-zA-Z]{3,10} \d{4}, \d{2}\:\d{2}', date)
#temp_date = re.search(r'\d\d\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}', date)

    self.date = date
    self.plink = plink
    self.sublink = sublink
    self.subpage = subpage
    self.msg = msg
    self.name = name
    self.title = title
    self.joindate = joindate
    self.ulink = ulink
    self.sig = sig
    self.edit = edit

def setup_db():
##setup mysql db

  mysql_host = host
  mysql_username = user
  mysql_password = passwd

  try:
    con = mdb.connect(mysql_host, mysql_username, mysql_password, 'forumsdb', charset='utf8')
    cur = con.cursor()
  except mdb.Error, e:
    print "Database Connection Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)

  return con, cur

def resume(home, sublinks, con, cur):
  f_id = get_id( cur, "FORUMS", "forum_url", home)
  default = [sublinks, "", "", 1, "", ""]
  print "f_id:", f_id
  if f_id==0:
    return default
  command = "SELECT postlink, thread_id FROM POSTS WHERE post_id=(SELECT MAX(post_id) FROM POSTS)" 
  cur.execute(command)
  t_junk = cur.fetchone()
  if t_junk is None:
    return default
  else:
    p_link, t_id = t_junk

  print "Resume scraping forum " + home + " at " + p_link

  command = "SELECT thread_name, subforum_id, subforum_page FROM THREADS WHERE thread_id="+str(t_id)
  cur.execute(command)
  t_name, s_id, s_page = cur.fetchone()
  command = "SELECT subforum_name, subforum_url FROM SUBFORUMS WHERE subforum_id="+str(s_id)
  cur.execute(command)
  s_name, s_url = cur.fetchone()
  
  i=0
  for subname, sublink in sublinks:
    if subname == s_name:
      return sublinks[i:], t_name, p_link, s_page, s_name, s_url
    i+=1
  
  print "Resume Error... Restarting scrape"
  print "Subforum: " + s_name
  print "Thread: " + t_name
  print "Link: " + t_link
  return default

def get_id( cur, table, id_name, name):
#This function gets the mysql generated id number of a row from a table
#INPUTS: Cur is a cursor object, table is a string that is the name of the table, id_name is the name of the column that is being searched, name is a string that is the name of the

  regex = re.compile(r'["\']')
  name = regex.sub('', name)
  command = "SELECT * FROM %s WHERE %s = \"%s\";" % (table, id_name, name)
#print command
  cur.execute(command)
  row = cur.fetchone()

  if row:
    return row[0]
  else:
    return 0

def insert_data(con, cur, post):
#print post
  f_id = get_id( cur, "FORUMS", "forum_url", post.home)
  if not f_id:
    #print "Forum id not found"
    cur.execute("INSERT INTO FORUMS (forum_name, forum_url) VALUES (%s, %s)", (post.home, post.home))
    con.commit()
    f_id = get_id(cur, "FORUMS", "forum_url", post.home)
    #print f_id


  sf_id = get_id( cur, "SUBFORUMS", "subforum_name", post.subname)
  if not sf_id:
#print "subForum id not found"
    cur.execute("INSERT INTO SUBFORUMS (subforum_name, forum_id) VALUES (%s, %s)", (post.subname, f_id))
    con.commit()
    sf_id = get_id(cur, "SUBFORUMS", "subforum_name", post.subname)
#print sf_id

  thread_id = get_id( cur, "THREADS", "thread_name", post.thread)
  if not thread_id:
    #print "thread id not found"
    cur.execute("INSERT INTO THREADS (thread_name, subforum_id, subforum_page) VALUES (%s, %s, %s)", (post.thread, sf_id, post.subpage))
    con.commit()
    thread_id = get_id(cur, "THREADS", "thread_name", post.thread)
    print "New THREAD: %s" % post.thread

  user_id = get_id( cur, "USERS", "username", post.name)
  if not user_id:
    #print "post id not found\nPOST MESSAGE: %s\n\n" % (post.msg)
    cur.execute("INSERT INTO USERS (forum_id, username, usertitle, joindate, sig) VALUES (%s, %s, %s, %s, %s)", (f_id, post.name, post.title, post.joindate, post.sig))
    con.commit()
    user_id = get_id(cur, "USERS", "username", post.name)
    #print post_id


  post_id = get_id( cur, "POSTS", "postlink", post.plink)
  if not post_id:
    #print "post id not found\nPOST MESSAGE: %s\n\n" % (post.msg)
    cur.execute("INSERT INTO POSTS (postdate, postlink, msg, edits, thread_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)", (post.date, post.plink, post.msg, post.edit, thread_id, user_id))
    con.commit()
    
    #post_id = get_id(cur, "POSTS", "postlink", post.plink)
    #print post_id

