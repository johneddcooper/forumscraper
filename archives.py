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
import multiprocessing
from multiprocessing import Queue
#import dblib

re_sort = re.compile(r"\d*(?=\.html)")
re_uid = re.compile(r"\d*$")
i = None

timeout = 10 
home = ""
archive_link = ""
q = Queue()

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

def get_thread_pages(br, link):
    """Given a thread link, returns individual thread's pagination."""
    punc = re.search(r'(\W)', link[::-1])
    # punc should always return something, or this link has no punctuation!
    
    assert punc
    
    if punc.groups()[0] == '.':
        # if link is in form "/thread-343.html" then strip the file ext
        stub = re.sub(r"^.*?\.", "", link[::-1])[::-1]    
    else:            
        # don't strip links in the form ?thread=2343 because often these
        # links have pages appended in the form of arguments
        stub = link
    
    urls = get_urls(br)
    candidates = filter(lambda url: url.startswith(stub), urls)
    pages = uniq(candidates)
    return pages

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

def uniq(li, generator=1):
    """like sort(list(li)) but preserves order. returns generator by default"""
    seen = set()
    seen_add = seen.add
    if generator:
        return (x for x in li if x not in seen and not seen_add(x))
    else:
        return [x for x in li if x not in seen and not seen_add(x)]

def get_threads(br):
    link = br.current_url
    urls = get_urls(br)
    # first get pages
    
    #pagination always starts with the same url as the subforum link, minus the file extension
    stub = re.sub(r"^.*?\.", "", link[::-1])[::-1]

    pages = filter(lambda url: url.startswith(stub) and not url.startswith(link), urls)
    
    # remove duplicates while preserving order
    pages = uniq(pages)
    
    yield get_threads_on_page(br, stub)
    for page in pages:
        #get threads
        #threads start with archive_link, but do not start with stub_template
        yield get_threads_on_page(br, stub)

def save_page(subforum, thread, page, source):
    # opens appropriate file handler
    #f = open( ... )
    #f.write(source)
    print "Saving page %s : %s : %s"
    print source[:30] + " ..."
    return

def worker(q):
    br = init_selenium()
    while True:
        try:
            job = q.get()
            if not job:
                break
            # front page of thread, so get links
            subforum, link = job
            if len(job) == 2:
                visit_page(br, link)
                thread = br.current_url
                thread_pages = get_thread_pages(br, link)
                print "Got thread pages from %s" % link
                for tp in thread_pages:
                    q.enqueue((subforum, thread, tp))
            elif len(job) == 3:
                print "Visited thread page %s" % link
                subforum, thread, link = job
                visit_page(br, link)
            else:
                # this should never happen
                print "Malformed job length. Job:", job

            source = br.page_source
            save_page(subforum, thread, link, source)
            
            q.task_done()
        except:
            print "no jobs enqueued. waiting..."
            sleep(10)

def init_workers(num, q):
    workers = []
    for i in xrange(num):
        tmp = multiprocessing.Process(target=worker, args=q)
        tmp.start()
        workers.append(tmp)
    for worker in workers:
        worker.join()
    print "All workers done."
    return q.empty()

if len(sys.argv) < 2:
    print "Usage: python progname.py link"

home = sys.argv[1]

archive_link = urlparse.urljoin(home, "/archive/index.php")
print archive_link
#atexit.register(save_state)

br = init_selenium()

visit_page(br, archive_link)
subforums = get_subforums(br)
initialized = False
for subforum in subforums:
    visit_page(br, subforum)
    sub_title = br.title
    if not br.current_url.startswith(archive_link):
        print "Skipping subforum: %s" % br.current_url
        continue
    for tl in get_threads(br):
        q.put((sub_title, tl))
        if not initialized:
            init_workers(5, q)
            initialized=True

    # debug
    pdb.set_trace()

visit_page(br, thread)

