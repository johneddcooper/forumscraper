"""This file parses vbulletin forums"""

import re
import logging
from BeautifulSoup import BeautifulSoup as bs
import imaget
import pdb

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


date_marker = ["<!-- status icon and date -->", "<!-- / status icon and date -->"]
message_marker = ["<!-- message -->", "<!-- / message -->"]
sig_marker = ["<!-- sig -->", "<!-- / sig -->"]
edit_marker = ["<!-- edit note -->", "<!-- / edit note -->"]



def get_subforums(main_soup):

    subforums = main_soup.findAll('td', attrs={'class':'alt1Active'})
    sublinks = []
    for s in subforums:
        links = s.findAll('a')
        for a in links:
            if not "http" in a['href']:
                break
        link = a['href']
        text = a.getText()
        sublinks.append({'name':text, 'link':link})

    return sublinks


def get_threads(subforum_soup):
    """This function gets information on the threads from the subforum page. It also returns the total number of pages"""
    threads = subforum_soup.findAll('a',  attrs={'id':lambda x:x and x.startswith('thread_title')}) #pulls out the thread links

    #page _ of _
    page = 1
    page_count = subforum_soup.find('td', attrs={'class':'vbmenu_control'})
    if page_count:
        page_count = page_count.getText()
        page_match = re.search(r'(\d+) .+? (\d+)', page_count)
        if page_match:
            page_count = int(page_match.group(2))
            page = int(page_match.group(1))
            logger.debug("get_threads: page_count = %d, page = %d" % (page_count, page))
        else:
            page_count = 1
            page = 1

    thread_counts = subforum_soup.findAll('td', attrs={'class':'alt2', 'title':lambda x:x and re.match(r'.+?: \d+?', x)})
    if len(threads) != len(thread_counts):
        logger.error('get_threads: thread-count mismatch. Threads = %d; thread_counts = %d' % (len(threads), len(thread_counts)))
        logger.debug('get_threads: threads = %s' % str(threads))
	logger.debug('get_threads: thread_counts = %s' % str(thread_counts))
    threadlinks = []
    for i in range(min(len(threads), len(thread_counts))):
        t = threads[i]
        c = thread_counts[i]
        sanatized = c['title'].replace(',', '')
        count = int(re.search(r'.+?: (\d+?) .+?: (\d+?)',sanatized).group(1)) + 1
        text = t.getText()
        link = t['href']
        threadlinks.append({'name':text, 'link':link, 'count':count})
    return threadlinks, (page, page_count)

def get_page(thread_url, pagenum):
    return thread_url + "&page=" + str(pagenum)

def get_posts(page_soup):

    page_soup = bs(page_soup)


    #page _ of _
    page_count = page_soup.find('td', attrs={'class':'vbmenu_control'})
    if page_count:
        page_count = page_count.getText()
        page_match = re.search(r'(\d+) .+? (\d+)', page_count)
        if page_match:
            page_count = int(page_match.group(2))
            page = int(page_match.group(1))
        else:
            page_count = 1
            page = 1
    posts = page_soup.findAll('table', attrs={'id':lambda x: x and re.match(r'post', x)})
    logging.info('get_post: got %d posts' % len(posts))
    post_list = []
    for p in posts:
        post_link = p.find('a', attrs={'name': lambda x: x and re.match(r'\d+', x)})['href']
        post_string = str(p)
        raw_message = extract(post_string, message_marker[0], message_marker[1])

        date = extract(post_string, date_marker[0], date_marker[1])
        date = strip_tags(date).strip()
        message = get_message(raw_message)
        sig = extract(post_string, sig_marker[0], sig_marker[1])
        edit = extract(post_string, edit_marker[0], edit_marker[1])

        msg_image_srcs = imaget.get_image_src(raw_message)
        if msg_image_srcs: msg_image_srcs = msg_image_srcs[0]
        print "message source: " 
        print msg_image_srcs
        print "\n\n\n"

        user = get_user(post_string, sig)

        post_list.append({'date': date, 'message': message, 'edit': edit, 'message images': msg_image_srcs, 'user': user, 'link': post_link})

    return post_list, (page, page_count)



def get_user(post_string, sig = ""):

    user_tag = bs(post_string).find('td', attrs={'class':'alt2'})
    user_link = user_tag.find('a', attrs={'class':'bigusername'})
    if not user_link: return {'tag': user_tag, 'name': 'guest', 'link': None, 'join': None, 'sig': None, 'image': None, 'title': 'guest'}
    user_name = user_link.getText()
    user_link = user_link['href']
    user_title = user_tag.findAll('div')[1].getText()
    
    user_div = user_tag.findAll('div')
    inner_ind = 2
    while len(user_div[inner_ind].findAll('div'))<3:
        inner_ind+=1
    inner_name_soup = user_div[inner_ind].findAll('div')
    join_date = inner_name_soup[0].getText()[len("Join Date: "):]

    user_image_src = imaget.get_image_src(user_tag, 1)

    return {'tag': user_tag, 'name':user_name, 'link': user_link, 'title': user_title, 'join': join_date, 'sig': sig, 'image': user_image_src}

    
    

def get_message(message_str):
    message_soup = bs(message_str)
    images = message_soup.findAll('img')
    for item in images:
      item.extract()
    scripts = message_soup.findAll('script')
    for item in scripts:
      item.extract()
    return str(message_soup)
    
        

def extract(string, start_marker, end_marker):
  """wrapper function for slicing into a string"""
  start_loc = string.find(start_marker)
  end_loc = string.find(end_marker)
  if start_loc == -1 or end_loc == -1:
    return ""
  return string[start_loc+len(start_marker):end_loc]

def strip_tags(source):
    return re.sub(r'<.+?>', '', source) 
