from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from subprocess import Popen, PIPE
from BeautifulSoup import BeautifulSoup as bs

import MySQLdb as mdb

import re, urlparse
import os, sys, getopt
import re, copy

from local_settings import *
import dblib

mysql_host = host
mysql_username = user
mysql_password = passwd

def usage():
  print "usage: vbscraper.py URL"

def parse_args():
  global home
  if len(sys.argv) < 2:
    usage()
    sys.exit(0)

  home = sys.argv[1]
  if home[-1] != '/':
    home = home + "/"
#if xte not recognized, run sudo apt-get install xautomation
def keypress(sequence):
  p=Popen(['xte'], stdin=PIPE)
  p.communicate(input=sequence)

def extract(string, start_marker, end_marker):
  start_loc = string.find(start_marker)
  end_loc = string.find(end_marker)
  if start_loc == -1 or end_loc == -1:
    return ""
  return string[start_loc+len(start_marker):end_loc]

#isolates the X from Page 1 of X on a given page
#only works on english
def getpages_vbulletin(soup):
  pages=1
  a = soup.findAll('a', attrs={'title':lambda x:x and x.startswith('Last Page')})
  if len(a)==0:
    a = soup.findAll('a', attrs={'title':lambda x:x and x.startswith('Show results')})
  
  if len(a) != 0:
    url = urlparse.urlparse(a[-1]['href'])
    params = urlparse.parse_qs(url.query)
    pages = int(params['page'][0])
  
  return pages

parse_args()
backtime = -1

##setup mysql db
con, cur = dblib.setup_db()

##initialize selenium
browser = webdriver.Firefox()
browser.set_page_load_timeout(5)
try:
  browser.get(home)
except TimeoutException:
  print "Timeout error: " + home
  keypress("Key Escape ")

##get subforums from main directory
main_src = browser.page_source

#strip html comments
main_src = re.sub("<!-+.*>?","", main_src)

main_soup = bs(main_src)
subforums = main_soup.findAll('td', attrs={'class':'alt1Active'})
sublinks = []
for s in subforums:
  links = s.findAll('a')
  for a in links:
    if not "http" in a['href']:
      break
  link = a['href']
  text = a.getText()
  sublinks.append((text, link))

##iterate through subforums
for subname, sublink in sublinks:

  #iterate through pages of subforum
  page = 1
  last_sub_title = ""
  sub_title = "test"
  while last_sub_title != sub_title:
    last_sub_title = sub_title
    try:
      ##go to subforum page, daysprune=-1: show all entries
      browser.get(home + sublink + '&daysprune=%s&page=%s' %(str(backtime), str(page)))
    except TimeoutException:
      print "Timeout: " + home + sublink + '&daysprune=' + str(backtime)
      keypress("key Escape ")
    src = browser.page_source
    soup = bs(src)
    sub_title= soup.title.string
    if sub_title == last_sub_title:
      break
    #get subforums
  
    threads = soup.findAll('a',  attrs={'id':lambda x:x and x.startswith('thread_title')})
    #scrape subforum
    
    for t in threads:
      #print t['href']
      #print "Total pages in thread:", thread_pages
      #now traverse all the pages in thread, downloading content
      thread_page = 1
      post = 0
      thread = [t.getText()]
      posts = []
      last_thread_title = ""
      thread_title = "title"
      while last_thread_title != thread_title:
        last_thread_title = thread_title
        #this contains both the header, which contains the date of the post, and the body, which contains
        #information about the user and the message
        try:
          browser.get(home + t['href'] + "&page=%s" % (str(thread_page)))
        except TimeoutException:
          print "Timeout: " + home + t['href']
          keypress("key Escape ")
        tsrc = browser.page_source
        tsoup = bs(tsrc)
        thread_title = tsoup.title.string

        if tsoup.title.string == last_thread_title:
          break
        
        blocksoup = tsoup.findAll('table', attrs={'id':lambda x:x and x.startswith('post')})
        
        #iterate through individual posts
        for i, block in enumerate(blocksoup):
          i+=1 #first post is 1
          trsoup = block.findAll('tr') #split block table
          header = trsoup[0].findAll('td')
          postdate = header[0].getText(' ')
          print "\n\n\nGrabbed Postdate: " + postdate
          print "Grabbed Header: " + str(header)
          postlink = header[1].findAll('a')[0]['href'] #index 1 returns the showthread link rather than showpost
          bodysoup = trsoup[1].findAll('td') #split body of message into username panel and post info
          
          userlinks = bodysoup[0].findAll('a', attrs={'class':'bigusername'})
          if len(userlinks) > 0:
            username = userlinks[0]
	    name = username.getText()
	    link = username['href']
          else:
            continue
	  #if name not in name database:
          usersoup=bodysoup[0].findAll('div')
          title = usersoup[1].getText()
          
	  inner_ind = 2
          while len(usersoup[inner_ind].findAll('div'))<3:
            inner_ind+=1
          innernamesoup = usersoup[inner_ind].findAll('div')
          joindate = innernamesoup[0].getText()[len("Join Date: "):]
          #postcount = innernamesoup[1].getText()[len("Posts: "):]
          sig = extract(block.prettify(), "<!-- sig -->", "<!-- / sig -->")
          #namebank[name] = [title, joindate, postcount, link, sig, []]
          #end if
          
          postchunks = bodysoup[1].findAll('div') #breaks into title, message, sig, and edits
          #print "Post " + str(i) + " by " + name
          #print "Link: " + postlink
          msg_extracted = extract(bodysoup[1].prettify(), "<!-- message -->", "<!-- / message -->")
          sig_extracted = extract(block.prettify(), "<!-- sig -->", "<!-- / sig -->")
          edit_extracted = extract(block.prettify(), "<!-- edit note -->", "<!-- / edit note -->")
          date_extracted = extract(block.prettify(), "<!-- status icon and date -->", "<!-- / status icon and date -->")
          
          P = dblib.post(home, subname, sublink, t.getText(), con.escape_string(date_extracted).decode("utf-8"), postlink, \
          con.escape_string(msg_extracted).decode("utf-8"), name, title, joindate, \
          link, con.escape_string(sig_extracted).decode("utf-8"), \
          con.escape_string(edit_extracted).decode("utf-8"))

          dblib.insert_data(con, cur, P)
          
          #cur.execute("""INSERT INTO FORUM_POSTS
          #(forum_name, subforum_name, thread_name, postdate, postlink, msg, username, usertitle,
          #joindate, userlink, sig, edits) 
          #VALUES
          #(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
          #(home, subname, t.getText(), postdate, postlink, \
          #con.escape_string(msg_extracted).decode("utf-8"), name, title, joindate, \
          #link, con.escape_string(sig_extracted).decode("utf-8"), \
          #con.escape_string(edit_extracted).decode("utf-8"))
          #)
          #con.commit()
          
        thread_page+=1
    
    #go to next page in subforum

#browser.close()
