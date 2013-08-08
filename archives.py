#!/usr/bin/env python
import re
import os
import sys
import signal
import atexit
import pickle
import time
from BeautifulSoup import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import urlparse
import subprocess
from collections import Counter
import pdb
#import dblib

re_sort = re.compile(r"\d*(?=\.html)")
re_uid = re.compile(r"\d*$")
i = None

timeout = 10 
home = ""
archive_link = ""

def init_selenium(profile=None):
    br = webdriver.Firefox(profile)
    br.set_page_load_timeout(timeout)
    return br

def send_esc(br):
    p = subprocess.Popen(["xdotool", "search", "--all", "--pid", str(br.binary.process.pid), "--name", "Mozilla Firefox", "key", "Escape"])

def visit_page(br, page):
    try:
        br.get(page)
    except TimeoutException:
        send_esc(br)

def interrupt(signal, frame):
    sys.exit(0)

def get_urls(br):
    raw_urls = []
    src = br.page_source
    soup = bs(src)
    for a in soup.findAll('a', href=True):
        raw_urls.append(urlparse.urljoin(archive_link, a['href']))
    return raw_urls


def strip_num(link):
    stripped = re.sub(r"\d+", "x", link)
    return stripped
    
def get_subforums(br):
    """gets all subforums from archive style homepage
    assumes subforum links are most common links on page,
    so may not work on forums with very few subforums
    """
    urls = get_urls(br)
    no_nums = map(strip_num, urls)
    ctr = Counter()
    for elem in no_nums:
        ctr[elem]+=1

    template = ctr.most_common(1)[0][0]
    subforums = filter(lambda x: strip_num(x)==template, urls)

    return subforums

def get_threads_on_page(br, stub):
    urls = get_urls(br)
    stub_template = strip_num(stub)
    no_nums = map(strip_num, urls)
    ctr = Counter()
    for elem in no_nums:
        if not elem.startswith(stub_template):
            ctr[elem]+=1

    thread_template = ctr.most_common(1)[0][0]
    page_threads = filter(lambda x: strip_num(x)==thread_template, urls)
    return page_threads

def get_threads(br):
    link = br.current_url
    urls = get_urls(br)
    # first get pages
    
    #pagination always starts with the same url as the subforum link, minus the file extension
    stub = re.sub(r"^.*?\.", "", link[::-1])[::-1]

    pages = filter(lambda url: url.startswith(stub) and not url.startswith(link), urls)
    
    # remove duplicates while preserving order
    seen = set()
    seen_add = seen.add
    pages = [x for x in pages if x not in seen and not seen_add(x)]
    
    threads = get_threads_on_page(br, stub)
    for page in pages:
        #get threads
        #threads start with archive_link, but do not start with stub_template
        visit_page(br, page)
        threads.extend(get_threads_on_page(br, stub))

    return threads

if len(sys.argv) < 2:
    print "Usage: python progname.py link"

home = sys.argv[1]

archive_link = urlparse.urljoin(home, "/archive/index.php")
print archive_link
#atexit.register(save_state)

br = init_selenium()

visit_page(br, archive_link)
subforums = get_subforums(br)
all_threads = []
sub_titles = []
for subforum in subforums:
    visit_page(br, subforum)
    sub_title = br.title
    if not br.current_url.startswith(archive_link):
        print "Skipping subforum: %s" % br.current_url
        continue
    thread_links = get_threads(br)
    if thread_links:
        all_threads.append(thread_links)
        sub_titles.append(sub_title)
        # send thread_links to queue
    break

visit_page(br, thread)
#if first punc from end is period:
#    strip to stub

