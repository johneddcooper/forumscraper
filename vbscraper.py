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
con = ""
cur = ""
striptags = re.compile(r'<.+?>')

def usage():
  print "usage: vbscraper.py URL"

def parse_args():
  global home
  if len(sys.argv) < 2:
    usage()
    sys.exit(0)

  home = sys.argv[1]
  if home[-1] != '/':
    home += "/"

def keypress(sequence):
  p=Popen(['xte'], stdin=PIPE)
  p.communicate(input=sequence)

def extract(string, start_marker, end_marker):
  start_loc = string.find(start_marker)
  end_loc = string.find(end_marker)
  if start_loc == -1 or end_loc == -1:
    return ""
  return string[start_loc+len(start_marker):end_loc]


def scrape_thread(url, thread, thread_page, subname, sublink):
  post = 0
  posts = []
  last_thread_title = ""
  thread_title = "title"
  while last_thread_title != thread_title:
    last_thread_title = thread_title
    #this contains both the header, which contains the date of the post, and the body, which contains
    #information about the user and the message
    try:
      browser.get(home + url + "&page=%s" % (str(thread_page)))
    except TimeoutException:
      print "Timeout: " + home + url
      keypress("key Escape ")
    tsrc = browser.page_source
    tsoup = bs(tsrc)
    if len(tsoup.title)==0:
      break
    
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
      postdate = striptags.sub('', postdate).strip(' \n')          
      #print "\n\n\nGrabbed Postdate: " + postdate
      #print "Grabbed Header: " + str(header)
      postlink = url+"&page="+str(thread_page)
      #postlink = header[1].findAll('a')[1]['href'] #index 1 returns the showthread link rather than showpost
      bodysoup = trsoup[1].findAll('td') #split body of message into username panel and post info
      
      userlinks = bodysoup[0].findAll('a', attrs={'class':'bigusername'})
      if len(userlinks) > 0:
        username = userlinks[0]
        name = username.getText()
        link = username['href']
      else:
        #Guest poster
        continue
      usersoup=bodysoup[0].findAll('div')
      title = usersoup[1].getText()
      
      inner_ind = 2
      while len(usersoup[inner_ind].findAll('div'))<3:
        inner_ind+=1
      innernamesoup = usersoup[inner_ind].findAll('div')
      joindate = innernamesoup[0].getText()[len("Join Date: "):]
      #postcount = innernamesoup[1].getText()[len("Posts: "):]
      sig = extract(block.prettify(), "<!-- sig -->", "<!-- / sig -->")
      
      postchunks = bodysoup[1].findAll('div') #breaks into title, message, sig, and edits
      msg_extracted = extract(bodysoup[1].prettify(), "<!-- message -->", "<!-- / message -->")
      sig_extracted = extract(block.prettify(), "<!-- sig -->", "<!-- / sig -->")
      edit_extracted = extract(block.prettify(), "<!-- edit note -->", "<!-- / edit note -->")
      date_extracted = extract(block.prettify(), "<!-- status icon and date -->", "<!-- / status icon and date -->") 
      P = dblib.post(home, subname, sublink, s_page, thread, con.escape_string(date_extracted).decode("utf-8"), postlink, \
      con.escape_string(msg_extracted).decode("utf-8"), name, title, joindate, \
      link, con.escape_string(sig_extracted).decode("utf-8"), \
      con.escape_string(edit_extracted).decode("utf-8"))
      dblib.insert_data(con, cur, P)
    thread_page+=1
parse_args()
backtime = -1

##initialize selenium
browser = webdriver.Firefox()
browser.set_page_load_timeout(5)
try:
  browser.get(home)
except TimeoutException:
  print "Timeout: " + home
  keypress("Key Escape ")

##get subforums from main directory
main_src = browser.page_source
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

##setup mysql db
con, cur = dblib.setup_db()

##attempt to resume last session
sublinks, start_tname, start_tlink, s_page, s_name, s_link = dblib.resume(home, sublinks, con, cur)

if start_tlink != "":
  try:
    t_page=int(start_tlink.split('page=')[1])
    start_tlink = start_tlink.split('&page=')[0]
  except:
    print "Potentially malformed start URL: " + start_tlink
  else:
    print "RESUME SCRAPING " + home
    print "RESUME THREAD: " + start_tlink + "(%s)"%start_tlink
    print "t_page:", t_page
    P = scrape_thread(start_tlink, start_tname, t_page, s_name, s_link)
    restart = True
else:
  restart = False
##iterate through subforums
for subname, sublink in sublinks:

  #iterate through pages of subforum
  last_sub_title = ""
  sub_title = "test"
  while last_sub_title != sub_title:
    last_sub_title = sub_title
    try:
      ##go to subforum page, daysprune=-1: show all entries
      browser.get(home + sublink + '&daysprune=%s&page=%s' %(str(backtime), str(s_page)))
    except TimeoutException:
      print "Timeout: " + home + sublink + '&daysprune=' + str(backtime)
      keypress("key Escape ")
    src = browser.page_source
    soup = bs(src)
    if len(soup.title)==0:
      break
    sub_title= soup.title.string
    if sub_title == last_sub_title:
      break
    #get subforums
  
    threads = soup.findAll('a',  attrs={'id':lambda x:x and x.startswith('thread_title')})
    
    if restart:
      for i, t in enumerate(threads):
        if t.getText() == start_tname:
          threads = threads[i+1:]
      restart=False
    #scrape subforum
    
    for t in threads:
      #print t['href']
      #print "Total pages in thread:", thread_pages
      #now traverse all the pages in thread, downloading content
      scrape_thread(t['href'], t.getText(), 1, subname, sublink)
    
    #go to next page in subforum

#browser.close()
