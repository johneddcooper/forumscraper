"""This file parses vbulletin forums"""

import re
import logging
from BeautifulSoup import BeautifulSoup as bs
import imaget

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

page_404 = ""

date_marker = ["<!-- status icon and date -->", "<!-- / status icon and date -->"]
message_marker = ["<!-- message -->", "<!-- / message -->"]
sig_marker = ["<!-- start: postbit_signature -->", "<!-- end: postbit_signature -->"]
edit_marker = ["<!-- edit note -->", "<!-- / edit note -->"]


def get_subforums(main_soup):
    print "getting subforums"
    links = main_soup.findAll('a', attrs={'href':lambda x:x and x.startswith('forum')})
    sublinks = []
    for link in links:
        print "Name: %s Link: %s" % (link.getText(), link['href'])
        sublinks.append({'name':link.getText(), 'link':link['href']})

    return sublinks


def get_page(thread_url, pagenum):
    return thread_url + "&page=" + str(pagenum)

def get_page_info(page_soup):
    page = 1
    page_current = page_soup.find('span', attrs={'class':'pagination_current'})
    page_count = page_soup.find('span', attrs={'class':'pages'})
    if page_current: page = int(page_current.getText())
    if page_count:
        print re.search(r'(\d+)', page_count.getText()).groups(0)[0]
        page_count = int(re.search(r'(\d+)', page_count.getText()).groups(0)[0])
    else: page_count = 1
    return page, page_count

def get_threads(subforum_soup):

    page, page_count = get_page_info(subforum_soup)

    threads = subforum_soup.findAll('a', attrs={'id':lambda x:x and x.startswith('tid')})
    thread_counts = subforum_soup.findAll('a', attrs={'href':lambda x:x and re.search(r'whoPosted\(\d+\)', x)})
    if len(threads) != len(thread_counts):
        logger.error('get_threads: thread-count mismatch. Threads = %d; thread_counts = %d' % (len(threads), len(thread_counts)))
        logger.debug('get_threads: threads = %s' % str(threads))
	logger.debug('get_threads: thread_counts = %s' % str(thread_counts))

    thread_links = []
    for i in range(min(len(threads), len(thread_counts))):
        t = threads[i]
        c = thread_counts[i]
        sanatized = c.getText().replace(',', '')
        count = int(sanatized)
        name = t.getText()
        link = t['href']
        thread_links.append({'name':name, 'link':link, 'count':count})
    return thread_links, (page, page_count)


def get_posts(page_soup):

    page_soup = bs(page_soup)

    page, page_count = get_page_info(page_soup)

    posts = page_soup.findAll('table', attrs={'id':lambda x: x and re.match(r'post', x)})
    logging.info('get_post: got %d posts' % len(posts))
    post_list = []
    for p in posts:
        print "type of p: %s" % type(p)
        p = bs(str(p))
        post_link = p.find('a', attrs={'name': lambda x: x and re.search(r'pid\d+', x)})
        print "post link: " + post_link
        if post_link: post_link = post_link['href']
        post_string = str(p)
        raw_message = str(p.find('div', attrs={'class':'post_body'}))

        date = p.find('td', attrs={'class':'tcat'})
        print date
        date = bs(str(date)).find('div').getext()
        date = strip_tags(date).strip()
        message = raw_message
        sig = extract(post_string, sig_marker[0], sig_marker[1])
        edit = None #extract(post_string, edit_marker[0], edit_marker[1])

        msg_image_srcs = None #imaget.get_image_src(raw_message)
        if msg_image_srcs: msg_image_srcs = msg_image_srcs[0]
        print "message source: " 
        print msg_image_srcs
        print "\n\n\n"

        user = None #get_user(post_string, sig)
        post_list.append({'date': date, 'message': message, 'edit': edit, 'message images': msg_image_srcs, 'user': user, 'link': post_link})

    return post_list, (page, page_count)
