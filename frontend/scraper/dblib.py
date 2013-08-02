"""This library provides functions to manipulate the database"""
import MySQLdb as mdb
import sys
from local_settings import *
import re
import logging
import pdb

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class post:
  """This object contains all of the information relevant to a post"""

  def __init__(self, home, subname, sublink, subpage, thread, date, plink, msg, name, title, joindate, ulink, sig, edit, images = []):
    """"Initialize the structure

	INPUT: string (forum homepage), string (name of subforum), string (link to subforum page),
		   int (subforum page), string (post's thread), string (date), string (link to post),
		   string (message content), string (username), string (user title), string (user join date),
		   string (user link), string (user signature), string (edit content), list of strings (image urls)
	RETURNS: post object"""

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
    self.images = images
    self.thread_id = 0
    logger.debug(" new post created\n\thome = %s\n\tdate = %s\n\tusername = %s\n images = %s", home, date, name, str(images))

def setup_db():
  """Setup mysql db

  INPUT: None
  RETURNS: None"""

  mysql_host = host
  mysql_username = user
  mysql_password = passwd

  try:
    con = mdb.connect(mysql_host, mysql_username, mysql_password, 'forumsdb', charset='utf8')
    cur = con.cursor()
  except mdb.Error, e:
    logger.error("Database Connection Error %d: %s", e.args[0], e.args[1])
    sys.exit(1)

  return con, cur

def resume(home, sublinks, con, cur):
  """Resumes scraping from previous stopping point

  INPUT: string (forum homepage), list of strings (links to subforums), MySQLdb Connection object
		 MySQLdb Cursor object
  RETURNS: list (subforum link, thread name, page link, start page, subforum name, subforum url)"""
  f_id = get_id( cur, "FORUMS", "forum_url", home)
  default = [sublinks, "", "", 1, "", ""]
  #print "f_id:", f_id
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
  logger.info("Resume scraping forum %s at %s", home, p_link)

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
  logger.error("Resume Error... Restarting scrape")
  print "Subforum: " + s_name
  print "Thread: " + t_name
  print "Link: " + t_link
  return default

"""
def last_insert_id(cur, con):

  command = "SELECT last_insert_id();"
  try:
    cur.execute(command)
  except: mdb.Error
    print "Error getting last inserted ID"
"""

def get_item(cur, table, col, id_name, ID):
    try:
        cur.execute("SELECT %s FROM %s WHERE %s = %s", col, table, id_name, ID)
        row = cur.fetchone()
        if row: return row[0]
    except mdb.Error:
        logger.error("Cannot finde item")
    return None
    

def get_id( cur, table, id_name, name):
  """This function gets the mysql generated id number of a row from a table

  INPUTS: MySQLdb Cursor object, string (table name), string (column name), string(search string)
  RETURNS: int (related ID or 0)"""

  regex = re.compile(r'["\']')
  name = regex.sub('', name)
  if id_name == "thread_name":  logger.debug("thread name: %s", name)
  command = "SELECT * FROM %s WHERE %s = \"%s\";" % (table, id_name, name)
  #print command
  try:
	  cur.execute(command)
	  row = cur.fetchone()
  except mdb.Error:
		print "ERROR: Cannot get %s for %s" % (id_name, name)
		logger.error("Cannot get %s for %s", id_name, name)
		return 0
  else:
	  if row:
			return row[0]
	  else:
			return 0


def link_images(con, cur, post_id):

    command = "SELECT msg FROM POSTS WHERE post_id = %s" % post_id
    try:
        cur.execute(command)
        row = cur.fetchone()
    except mdb.Error:
        print "ERROR: Cannot get msg for %s" % post_id
        logger.error("Cannot get msg for %s", post_id)
        return 0
    else:
        if not row:
            print "ERROR: no msg for post %s" % post_id
            return 0
        else:
            msg = row[0]
            print msg
            return


def get_forum_id(con, cur, url):

    f_id = get_id(cur, "FORUMS", "forum_url", url)
    if not f_id:
		#print "Forum id not found"
		try:
			cur.execute("INSERT INTO FORUMS (forum_name, forum_url) VALUES (%s, %s)", (url, url))
			con.commit()
		except:
			print "ERROR: Could not add %s into forums table" % url
			logger.error("Could not add %s into forums table", url)
			return 1
		f_id = get_id(cur, "FORUMS", "forum_url", url)
    return f_id


def get_sub_id(con, cur, sub, f_id):
    regex = re.compile(r'["\']')
    sub = regex.sub('', sub)
    sf_id = get_id( cur, "SUBFORUMS", "subforum_name", sub)
    if not sf_id:
		#print "subForum id not found"
		try:
			cur.execute("INSERT INTO SUBFORUMS (subforum_name, forum_id) VALUES (%s, %s)", (sub, f_id))
			con.commit()
		except:
			print "ERROR: Could not add %s into subforums table" % sub
			logger.error("Could not add %s into subforums table", sub)
			return 1
		sf_id = get_id(cur, "SUBFORUMS", "subforum_name", sub)
    return sf_id

def get_thread_id(con, cur, thread, sf_id):
    regex = re.compile(r'["\']')
    thread = regex.sub('', thread)
    thread_id = get_id( cur, "THREADS", "thread_name", thread)
    if not thread_id:
		#print "thread id not found"
		try:
			cur.execute("INSERT INTO THREADS (thread_name, subforum_id) VALUES (%s, %s)", (thread, sf_id))
			con.commit()
		except:
			print "ERROR: Could not add %s into threads table" % thread
			logger.error("Could not add %s into threads table", thread)
                        raise
			return 1
		thread_id = get_id(cur, "THREADS", "thread_name", thread)
    return thread_id

def insert_data(con, cur, post):
  """Inserts the data into the database

  INPUTS: MySQLdb Connection object, MySQLdb Cursor object, Post object
  RETURNS: tuple (post id, user id)"""
  #print post
  f_id = get_id( cur, "FORUMS", "forum_url", post.home)
  if not f_id:
		#print "Forum id not found"
		try:
			cur.execute("INSERT INTO FORUMS (forum_name, forum_url) VALUES (%s, %s)", (post.home, post.home))
			con.commit()
		except:
			print "ERROR: Could not add %s into forums table" % post.home
			logger.error("Could not add %s into forums table", post.home)
			return (0, 0)
		f_id = get_id(cur, "FORUMS", "forum_url", post.home)
  #print f_id


  sf_id = get_id( cur, "SUBFORUMS", "subforum_name", post.subname)
  if not sf_id:
		#print "subForum id not found"
		try:
			cur.execute("INSERT INTO SUBFORUMS (subforum_name, forum_id) VALUES (%s, %s)", (post.subname, f_id))
			con.commit()
		except:
			print "ERROR: Could not add %s into subforums table" % post.subname
			logger.error("Could not add %s into subforums table", post.subname)
			return (0, 0)
		sf_id = get_id(cur, "SUBFORUMS", "subforum_name", post.subname)
  #print sf_id

  thread_id = get_id( cur, "THREADS", "thread_name", post.thread)
  if not thread_id:
		#print "thread id not found"
                pdb.set_trace()
		try:
			cur.execute("INSERT INTO THREADS (thread_name, subforum_id) VALUES (%s, %s)", (post.thread, sf_id))
			con.commit()
		except:
			print "ERROR: Could not add %s into threads table" % post.thread
			logger.error("Could not add %s into threads table", post.thread)
			return (0, 0)
		thread_id = get_id(cur, "THREADS", "thread_name", post.thread)
  		#print "New THREAD: %s" % post.thread
  post.thread_id = thread_id


  user_id = get_id( cur, "USERS", "username", post.name)
  if not user_id:
		#print "post id not found\nPOST MESSAGE: %s\n\n" % (post.msg)
		try:
			cur.execute("INSERT INTO USERS (forum_id, username, usertitle, joindate, sig) VALUES (%s, %s, %s, %s, %s)", (f_id, post.name, post.title, post.joindate, post.sig))
			con.commit()
		except:
			print "ERROR: Could not add %s into users table" % post.name
			logger.error("Could not add %s into users table", post.name)
			return (0, 0)
		user_id = get_id(cur, "USERS", "username", post.name)
  #print post_id
  post_id = get_id( cur, "POSTS", "postlink", post.plink)
  if not post_id:
		#print "post id not found\nPOST MESSAGE: %s\n\n" % (post.msg)
		try:
			cur.execute("INSERT INTO POSTS (postdate, postlink, msg, edits, thread_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)", (post.date, post.plink, post.msg, post.edit, thread_id, user_id))
			con.commit()
		except mdb.Error:
			print "ERROR: Could not add %s into posts table" % post.plink
			logger.error("Could not add %s into posts table", post.plink)
			print post.date
                        raise
			return (0, 0)
		post_id = get_id(cur, "POSTS", "postlink", post.plink)
  print "post images: "
  print post.images
  if not post.images: return (post_id, user_id)
  for image in post.images:
  	image_id = get_id(cur, "IMAGES", "image_src", image)
  	if not image_id:
  		try:
  			cur.execute("INSERT INTO IMAGES (thread_id, user_id, post_id, image_src) VALUES (%s, %s, %s, %s)", (thread_id, user_id, post_id, image))
  			con.commit()
			print "ADDED IMAGE TO DB"
		except mdb.Error:
			print "ERROR: Could not add %s into images table" % image
			logger.error("Could not add %s into images table", image)
			print post.date
			continue
  	image_id = get_id(cur, "IMAGES", "image_src", image)
        print "ADDED IMAGE %s to POST %s by USER %s" % (image_id, post_id, user_id)

  return (post_id, user_id)


def get_thread_count(thread_name, cur):

    logger.info("in get_thread_count")
    thread_id = get_id( cur, "THREADS", "thread_name", thread_name)
    if not thread_id: return 0
    try:
        cur.execute("SELECT COUNT(post_id) FROM POSTS WHERE thread_id = %s", thread_id)
        row = cur.fetchone()
        if row: 
            logger.debug("There were %d posts in the thread", row[0])
            return row[0]
        else:
            logger.debug("There were 0 posts in the thread")
            return 0
    except mdb.error: 
        print "SUPER ERROR"
        logger.error("There was an error getting the thread count")
        raise
        return 0
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

