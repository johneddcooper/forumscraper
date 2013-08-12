#!/usr/bin/python2
"""This module contains the scraper and parses the data"""
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from subprocess import Popen, PIPE
from BeautifulSoup import BeautifulSoup as bs

import MySQLdb as mdb

import re, urlparse
import os, sys, getopt
import copy
import logging
from local_settings import *
import dblib, imaget
import pickle
import restart
import vbulletin, mybb
import signal
import pdb

logging.basicConfig(filename='scraper.log',level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

mysql_host = host
mysql_username = user
mysql_password = passwd
striptags = re.compile(r'<.+?>')

kill_me = None

type_flag = 0

session_data = []

def usage():
  print "usage: vbscraper.py URL"

def parse_args():
  global home
  global type_flag
  if len(sys.argv) <3:
    usage()
    sys.exit(0)

  home = sys.argv[1]
  if home[-1] != '/':
    home += "/"
  logger.info("Home url: %s", home)

  type_flag = int(sys.argv[2])
  return home

def dead():
    kill_me.close()
    sys.stderr.write("EXITING")

def term_handler(signum, frame):
    dead()
    

def get_pickle_dir():
    home = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))
    parent = os.path.abspath(os.path.join(home, ".."))
    pickle_dir = os.path.join(parent, "pickles")
    if not os.path.exists(pickle_dir): os.mkdir(pickle_dir)
    return pickle_dir

def save_session_data():
    logger.info("saving session data")
    pickle_dir = get_pickle_dir()
    logger.debug("Pickle directory: %s", pickle_dir)
    pickle_file = open(os.path.join(pickle_dir, imaget.get_forum_name(session_data[0]) + ".p"), 'wb')
    pickle.dump(session_data, pickle_file)
    pickle_file.close()
    logger.info("dumped session data")
    return

def keypress(br):
  """This function emulates a keypress.

  It is called whenever the browser times out to prod it into continuing."""
  p=Popen(['xdotool', 'search', '--all', '--pid', str(br.binary.process.pid), "--name", "Mozilla Firefox", "key", "Escape"])
  p.communicate()

  logger.debug("sent escape keypress")

def extract(string, start_marker, end_marker):
  """wrapper function for slicing into a string"""
  start_loc = string.find(start_marker)
  end_loc = string.find(end_marker)

  logger.debug("extracting from string\nstart marker: %s\nend marker: %s\n string: %s", 
               start_marker, end_marker, string)
  if start_loc == -1 or end_loc == -1:
    return ""
  logger.debug("extracted string %s", string[start_loc+len(start_marker):end_loc])

  return string[start_loc+len(start_marker):end_loc]


def scrape_thread(browser, home, con, cur):
    """This function handles the main loop and parses the data obtained

  INPUTS: string (path to image directory), Selenium Browser object, string (subforum page), string (home url),
  string (thread name), int (thread page), string (subforum name), string (subforum link), 
  MySQLdb Connection Object, MySQLdb Cursor object.
  RETURNS: None"""
    forum_id = dblib.get_forum_id(con, cur, home)
    logger.info("got forum id %d", forum_id)
    restart.restore_state(forum_id)
    try:
        browser.get(home)
    except TimeoutException:
        logger.info("Timeout: %s", home)
        sys.stderr.write("TIMEOUT")
        keypress(browser)

    if type_flag:
        scraper = mybb
        logger.info("using mybb backend")
    else:
        scraper = vbulletin
        logger.info("using vbulletin backend")

    main_src = browser.page_source
    main_soup = bs(main_src)
    subforums = scraper.get_subforums(main_soup)

    logger.debug("got subforums: %s", str(subforums))

    subs = 0


    restart.get_cookies(forum_id, browser)

    sys.stderr.write("REFRESH")
    restart.dump_cookies(forum_id, browser)

    ##SUBFORUMS##
    for sub in subforums[::-1]:
        
        print "subforums %f%% DONE" % (float(subs)/len(subforums))
        print "subforum %d of %d DONE" % (subs, len(subforums))
        logger.info("subforums %f%% DONE", float(subs)/len(subforums))
        logger.info("subforum %d of %d DONE", subs, len(subforums))
        subs += 1
        subforum_id = dblib.get_sub_id(con, cur, sub['name'], forum_id)
        logger.debug("scraping subforum %s, id #%d", sub['name'], subforum_id)
        
        t_done = 0
        sub_page = 0
        sub_page_count = 1
        while sub_page < sub_page_count: #iterate through subforum pages
            sys.stderr.write("REFRESH")
            sub_page += 1
            sub_link = scraper.get_page(home + sub['link'], sub_page)
            print "sub link %s DONE" % sub_link
            logger.info("sub link %s DONE", sub_link)
            try:
                browser.get(sub_link)
            except TimeoutException:
                logger.info("Timeout: %s", home)
                sys.stderr.write("TIMEOUT")
                keypress(browser)
    
            sub_src = browser.page_source
            sub_soup = bs(sub_src)
            threads, (sub_page, sub_page_count) = scraper.get_threads(sub_soup)
            print "got threads"
            logger.debug("got threads\nsubforum page: %d\nsubforum poge count: %d\nThreads: %s", sub_page, sub_page_count, str(threads))

            ##THREADS##
            for thread in threads: #iterate through threads on page
                print "threads %f%% DONE" % (float(t_done)/(len(threads) * sub_page_count))
                print "thread %d of %d DONE" % (t_done, len(threads) * sub_page_count)
                logger.info("threads %f%% DONE", float(t_done)/(len(threads) * sub_page_count))
                logger.info("thread %d of %d DONE", t_done, len(threads) * sub_page_count)
                t_done += 1
                sys.stderr.write("REFRESH")
                thread_id = dblib.get_thread_id(con, cur, thread['name'], subforum_id)

                logger.debug("scraping thread %s, id %d", thread['name'], thread_id)
    
                tc = dblib.get_thread_count(thread['name'], cur)
                logger.debug("posts in thread: %d\ndownloaded posts from thread: %d", tc, thread['count'])
                if (thread['count'] == tc) and (tc != 0):  continue #if we have all of the posts, skip this thread

                if thread_id in restart.threads.keys(): logger.debug("in thread_keys: starting thread %d  scrape at %d", thread_id, restart.threads[thread_id])
                #    restart.threads[thread_id][1] += 1
                #else: restart.threads[thread_id] = (0, 1)
                else: 
                    restart.threads[thread_id] = 1
                    logger.debug("not in thread keys: starting thread %d scrape at page 1", thread_id)
                
                thread_page = restart.threads[thread_id] -1
                thread_page_count = thread_page + 1
                print "thread %d: page %d of %d" % (thread_id, thread_page, thread_page_count)
                print "%d\% done"
                while thread_page < thread_page_count: #iterate through thread pages
                    sys.stderr.write("REFRESH")
                    thread_page += 1
                    thread_link = scraper.get_page(home + thread['link'], thread_page)
                    logger.info("thread %d: page %d of %d\nLink: %s", thread_id, thread_page, thread_page_count, thread_link)
                    try:
                        browser.get(thread_link)
                    except TimeoutException:
                        logger.info("Timeout: %s", home)
                        sys.stderr.write("TIMEOUT")
                        keypress(browser)

                    page_src = browser.page_source
                    posts, (thread_page, thread_page_count) = scraper.get_posts(page_src)
                    print "got posts"
                    for post in posts:
                        print "iterate post"
                        user = post['user']
                        P = dblib.post(home, sub['name'], sub['link'], sub_page, thread['name'], post['date'], post['link'], post['message'],
                                      user['name'], user['title'], user['join'], user['link'], user['sig'], post['edit'], post['message images'])
                        (post_id, user_id) = dblib.insert_data(con, cur, P)
                        print post_id
                        print user['image']
                        print type(user['image'])
                        if user['image']:
                            if (user['image'].find('http') == -1): user['image'] = P.home + user['image']
                        imaget.get_user_image(user_id, user['image'])
                        imaget.get_post_images(P, post['message images'], cur)

                    #restart.threads[thread_id][0] = thread_page
                    restart.threads[thread_id] = thread_page
                    restart.save_state(forum_id)
                  
            
    """
  global session_data
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
      logger.info("Timeout: %s", home + url)
      sys.stderr.write("TIMEOUT")
      keypress("key Escape ")
    tsrc = browser.page_source
    tsoup = bs(tsrc)
    if len(tsoup.title)==0:
      logger.info("FINISHED SCRAPING FORUM %s", home)
      break
    
    thread_title = tsoup.title.string

    if tsoup.title.string == last_thread_title:
      logger.info("FINISHED SCRAPING FORUM %s", home)
      break
    
    blocksoup = tsoup.findAll('table', attrs={'id':lambda x:x and x.startswith('post')})
    
    #iterate through individual posts
    for i, block in enumerate(blocksoup):
      i+=1 #first post is 1
      trsoup = block.findAll('tr') #split block table
      header = trsoup[0].findAll('td')
      print "Grabbed header: "
      print header
      postdate = str(header[0])
      #print "Grabbed Header: " + str(header)
      #postlink = url+"&page="+str(thread_page)
      postlink = header[1].findAll('a')
      print postlink
      postlink = postlink[0]['href'] #index 1 returns the showthread link rather than showpost
      bodysoup = trsoup[1].findAll('td') #split body of message into username panel and post info
      
      userlinks = bodysoup[0].findAll('a', attrs={'class':'bigusername'})
      userpic_src = imaget.get_image_src(bodysoup[0], 1) #get the source for the user's picture
      postdate = striptags.sub('', postdate).strip()
      print "\n\n\nGrabbed Postdate: " + postdate
      if userpic_src: userpic_src = home + userpic_src
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
      msg_image_stc = []
      tmp_message = ""
      msg_image_src, temp_msg = imaget.get_image_src(bodysoup[1])
      msg_extracted = extract(temp_msg, "<!-- message -->", "<!-- / message -->")
      sig_extracted = extract(block.prettify(), "<!-- sig -->", "<!-- / sig -->")
      edit_extracted = extract(block.prettify(), "<!-- edit note -->", "<!-- / edit note -->")
      date_extracted = extract(block.prettify(), "<!-- status icon and date -->", "<!-- / status icon and date -->") 
      P = dblib.post(home, subname, sublink, s_page, thread, con.escape_string(postdate).decode("utf-8"), postlink, \
      con.escape_string(msg_extracted).decode("utf-8"), name, title, joindate, \
      link, con.escape_string(sig_extracted).decode("utf-8"), \
      con.escape_string(edit_extracted).decode("utf-8"), msg_image_src)
      (post_id, user_id) = dblib.insert_data(con, cur, P)
      imaget.get_user_image(user_id, image_dir, userpic_src)
      imaget.get_post_images(P, image_dir, msg_image_src, cur)
      sys.stderr.write("REFRESH")
      session_data = [home, url + "&page=%s" % str(thread_page), 0]
      save_session_data()
    thread_page+=1
    """
def init_browser():
    browser = webdriver.Firefox()
    browser.set_page_load_timeout(5)
    return browser

def main():

        global kill_me
        print "starting"
        home = parse_args()
        backtime = -1

        signal.signal(signal.SIGTERM, dead)
        image_dir = imaget.create_image_dir("images")

        ##initialize selenium
        browser = init_browser()
        ##setup mysql db
        con, cur = dblib.setup_db()

        kill_me = browser
        try:
            scrape_thread(kill_me, home, con, cur)
        except:
            pdb.post_mortem()
            dead()
            raise

        print "done"
        """
        try:
            browser.get(home)
        except TimeoutException:
            print "Timeout: " + home
            sys.stderr.write("TIMEOUT")
            keypress("Key Escape ")

        ##get subforums from main directory
        main_src = browser.page_source
        sys.stderr.write("REFRESH")
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
                P = scrape_thread(image_dir, browser, s_page, start_tlink, start_tname, t_page, s_name, s_link, con, cur)
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
                    scrape_thread(image_dir, browser, s_page, t['href'], t.getText(), 1, subname, sublink, con, cur)
                
                #go to next page in subforum

        #browser.close()
             """

if __name__ == "__main__":
    main()
