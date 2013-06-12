import MySQLdb as mdb
from local_settings import *

class post:

  def __init__(self, home, subname, thread, date, plink, msg, name, title, joindate, ulink, sig, edit):

    self.home = home
    self.subname = subname
    self.thread = thread
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

def insert_data(con, cur, post):

  print post

  cur.execute("""INSERT INTO FORUM_POSTS
            (forum_name, subforum_name, thread_name, postdate, postlink, msg, username, usertitle,
            joindate, userlink, sig, edits) 
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (post.home, post.subname, post.thread, post.date, post.plink, \
            post.msg, post.name, post.title, post.joindate, \
            post.ulink, post.sig, \
            post.edit)
            )
  con.commit()

