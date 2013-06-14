import MySQLdb as mdb
import sys
from local_settings import *
import re

class post:

  def __init__(self, home, subname, thread, date, plink, msg, name, title, joindate, ulink, sig, edit):

    self.home = home
    self.subname = subname
    self.thread = thread

    temp_date = re.search(r'\d+?[a-zA-Z]{2} [a-zA-Z]{3,10} \d{4}, \d{2}\:\d{2}', date)
    #temp_date = re.search(r'\d\d\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}', date)
    date = temp_date.group(0)

    self.date = date
    self.plink = plink
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
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)

  return con, cur

def get_id(cur, table, id_name, name):
  #This function gets the mysql generated id number of a row from a table
	#INPUTS: Cur is a cursor object, table is a string that is the name of the table, id_name is the name of the column that is being searched, name is a string that is the name of the
 
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

  f_id = get_id(cur, "FORUMS", "forum_url", post.home)
  if not f_id:
		#print "Forum id not found"
		cur.execute("INSERT INTO FORUMS (forum_name, forum_url) VALUES (%s, %s)", (post.home, post.home))
		con.commit()
		f_id = get_id(cur, "FORUMS", "forum_url", post.home)
  #print f_id


  sf_id = get_id(cur, "SUBFORUMS", "subforum_name", post.subname)
  if not sf_id:
		#print "subForum id not found"
		cur.execute("INSERT INTO SUBFORUMS (subforum_name, forum_id) VALUES (%s, %s)", (post.subname, f_id))
		con.commit()
		sf_id = get_id(cur, "SUBFORUMS", "subforum_name", post.subname)
  #print sf_id

  thread_id = get_id(cur, "THREADS", "thread_name", post.thread)
  if not thread_id:
		#print "thread id not found"
		cur.execute("INSERT INTO THREADS (thread_name, subforum_id) VALUES (%s, %s)", (post.thread, sf_id))
		con.commit()
		thread_id = get_id(cur, "THREADS", "thread_name", post.thread)
  #print thread_id

  user_id = get_id(cur, "USERS", "username", post.name)
  if not user_id:
		#print "post id not found\nPOST MESSAGE: %s\n\n" % (post.msg)
		cur.execute("INSERT INTO USERS (username, usertitle, joindate, sig) VALUES (%s, %s, %s, %s)", (post.name, post.title, post.joindate, post.sig))
		con.commit()
		user_id = get_id(cur, "USERS", "username", post.name)
  #print post_id


  post_id = get_id(cur, "POSTS", "postlink", post.plink)
  if not post_id:
		#print "post id not found\nPOST MESSAGE: %s\n\n" % (post.msg)
		cur.execute("INSERT INTO POSTS (postdate, postlink, msg, edits, thread_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)", (post.date, post.plink, post.msg, post.edit, thread_id, user_id))
		con.commit()
		post_id = get_id(cur, "POSTS", "postlink", post.plink)
  #print post_id

  #if not get_id(cur, "THREADS", "thread_name", "dick f"):

  #cur.execute("""INSERT INTO FORUM_POSTS
  #          (forum_name, subforum_name, thread_name, postdate, postlink, msg, username, usertitle,
  #          joindate, userlink, sig, edits) 
  #          VALUES
  #          (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
  #          (post.home, post.subname, post.thread, post.date, post.plink, \
  #          post.msg, post.name, post.title, post.joindate, \
  #          post.ulink, post.sig, \
  #          post.edit)
  #          )
  #con.commit()

