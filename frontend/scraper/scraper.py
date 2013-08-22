#!/usr/bin/env python
import re
import os
import sys
import signal
import atexit
from time import sleep
import urlparse
import subprocess
from collections import Counter, defaultdict
import pdb
import multiprocessing
from multiprocessing import Value
import logging
import cPickle
import argparse
import random

import MySQLdb as mdb

from BeautifulSoup import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from redis import Redis
from hotqueue import HotQueue

from parsers import *
from local_settings import *
import dblib
import gc

#gc.set_debug(gc.DEBUG_LEAK)
mysql_host = host
mysql_username = user
mysql_password = passwd

generic = False 
vbulletin = False
#archives = False

re_sort = re.compile(r"\d*(?=\.html)")
re_uid = re.compile(r"\d*$")
i = None

timeout = 10 
home = ""
hdir = ""
archive_link = ""
P = None
state = [0, 0] 
pfile = ""
save_files = False
con, cur = dblib.setup_db()

delay = 0
delay_range = 0

def parse_args(args):
    parser = argparse.ArgumentParser(description="Scrape a forum", add_help=False)
    parser.add_argument("url")
    parser.add_argument("num")
    parser.add_argument("--authfile")
    parser.add_argument("--delay", type=int)
    parser.add_argument("--delay_range", type=int)
    parser.add_argument("--save_files", action="store_true")
    type_scrape = parser.add_mutually_exclusive_group(required=True)
    #type_scrape.add_argument("--archives", action="store_true")
    type_scrape.add_argument("--vbulletin", action="store_true")
    type_scrape.add_argument("--generic", action="store_true")
    return parser.parse_args(args)

def init_logger():
    logging.basicConfig(filename='%s.log'%home,level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

def clear_queue():
    q = HotQueue(home)
    qf = HotQueue(home + "_sources")
    q.clear()
    qf.clear()
    os.remove(pfile)

def save_state():
    with open(pfile, "w") as f:
        cPickle.dump(state, f)

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
    
    urls = get_urls(br)
    if punc.groups()[0] == '.':
        # if link is in form "/thread-343.html" then strip the file ext
        stub = re.sub(r"^.*?\.", "", link[::-1])[::-1]    
        candidates = filter(lambda url: url.startswith(stub), urls)
        pages = uniq(candidates, generator=False)
        return pages
    else:            
        # don't strip links in the form ?thread=2343 because often these
        # links have pages appended in the form of arguments
        candidates = filter(lambda url: re.search(r"(&page=)", url), urls)
        if candidates:
            page_nums = [int(re.search(r"(?<=&page=)(\d*)", url).groups()[-1]) for url in candidates]
            max_page = max(page_nums)
            return [link + "&page=%d"%i for i in range(2, max_page+1)]
        else:
            candidates = filter(lambda url: re.search(r"(&start=)", url), urls)
            if not candidates:
                return
            page_nums = [int(re.search(r"(?<=&start=))(\d*)", url).groups()[-1]) for url in candidates]
            page_nums = sorted(set(list(page_nums)))
            step = page_nums[0]
            return [link + "&start=%d" % i for i in range(step, page_nums[-1], step)]

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

def add_to_database(subforum, link, post):
    # post is a defaultdict that defaults to ""
    post['home'] = home
    post['subname'] = subforum#.decode('utf8')
    post['thread'] = link 
    if not post['plink']:
        post['plink'] = link 
    dblib.insert_data(con, cur, post)

def scout(q):
    br = init_selenium()

    visit_page(br, archive_link)
    subforums = get_subforums(br)
    initialized = False
    for subforum in subforums[state[0]:]:
        visit_page(br, subforum)
        sub_title = br.title
        if not br.current_url.startswith(archive_link):
            logger.debug("Skipping subforum: %s" % br.current_url)
            continue
        for i, tl in enumerate(get_threads(br)):
            if i >= state[1]:
                # [q.put(cPickle.dumps((sub_title.encode('utf8'), thread))) for thread in tl]
                [q.put((sub_title.encode('utf8'), thread)) for thread in tl]
                state[1]+=1
            i += 1
        state[1] = 0
        state[0] += 1
    gc.collect()
    return

def parser(qf, qt):
    global training, P
    contents = qf.get()
    tic = 0
    while contents != "-sentinel-":
        tic += 1
        if tic >= 100:
            gc.collect()
            tic = 0
        if not contents:
            contents = qf.get()
            continue
        sf, link, src = contents
        #sf, link, src = cPickle.loads(contents)
        logger.debug("Parsing link %s" %link)
        if generic and not P.ready:
            # if adding this source pushes P over the training data threshold,
            # it will return the last five pages' parsed
            if P.add_source(src):
                qt.value=True
                results = P.train_and_parse()
                qt.value=False
                for pages in results:
                    for post in pages:
                        add_to_database(sf, link, post)
        else: 
            posts = P.parse(src)
            if not posts:
                logger.error("No post data. Weird.")
                # dump source to log file?
                logger.error(src)
            else:
                for post in posts:
                    add_to_database(sf, link, post)

        contents = qf.get()

def save_file(subforum, link, source, qf):
    global training
    subforum = subforum.decode('utf8').encode('utf8')
    soup = bs(source)
    hlink = re.sub("/", "", link)
    if save_files:
        f = open("%s/%s" % (hdir, hlink), "w")
        f.write(soup.renderContents())
        f.flush()
        f.close()
    #contents = cPickle.dumps((subforum.encode('utf8'), link, source.encode('utf8')))
    qf.put((subforum, link, source))

def worker(q, qf, qt, d, dr):


    br = init_selenium()
    for job in q.consume(timeout=5):
        if (d and dr) and (d >= dr):
            delay = random.triangular(d-dr, d+dr)
            print "delay is: " + str(delay)
            sleep(delay)
        else:
            print "Delay and dr not set"
        if not job:
            break
        # front page of thread, so get links
        #job = cPickle.loads(pick)
        if len(job) == 2:
            subforum, link = job
            visit_page(br, link)
            thread = br.current_url
            thread_pages = get_thread_pages(br, link)
            if thread_pages:
                for tp in thread_pages:
                    # contents = cPickle.dumps((subforum, thread, tp))
                    q.put((subforum, thread, tp)) 
        elif len(job) == 3:
            subforum, thread, link = job
            visit_page(br, link)
        else:
            # this should never happen
            logger.error("Malformed job length. Job:%s"%job)
        source = br.page_source
        while qt.value:
            sleep(1)
        logger.info("Saving page %s" % link)
        save_file(subforum, link, source, qf)
    qf.put("-sentinel-") # sentinel

def init_workers(num):
    global scout, worker, parser
    
    # q contains list of threads, scraped by the scout
    q = HotQueue(home)

    # qf contains list of tuples of len 3
    # contains source code of scraped pages and metadata, for parser
    # (subforum name, link of post, post source)
    qf = HotQueue(home + "_sources")
    
    # boolean variable that describes whether the Parser is training
    # (only used for GenericParser)
    qt = Value('b', False)
    
    workers = []
    scout = multiprocessing.Process(target=scout, args=(q,))
    scout.start()
    logger.info("Starting scout process %s" % str(scout.pid))
    workers.append(scout)
    sleep(15)
    for i in xrange(num):
        tmp = multiprocessing.Process(target=worker, args=(q,qf,qt,delay, delay_range))
        tmp.start()
        logger.info("Starting worker process %s" % str(tmp.pid))
        workers.append(tmp)
    logger.info("Using main process as parser.")
    parser(qf,qt)
    for worker in workers:
        worker.join()
    logger.info("All done.")
    q.clear()
    qf.clear()

args = parse_args(sys.argv[1:])
home = args.url

if args.delay:
    print args.delay
    delay = args.delay
if args.delay_range:
    delay_range = args.delay_range
    print args.delay_range

#q = JoinableQueue()
save_files = args.save_files

home = re.sub("/$", "", home)
home = re.sub("^http://", "", home)
hdir = "./" + home
if save_files and not os.path.isdir(hdir):
        os.mkdir(hdir)
pfile = hdir[2:] + ".p"


try:
    with open(pfile, "r") as f:
        state = cPickle.load(f)
    if args.generic:
        generic = True
        P = GenericParser(name=home,save=True)
except:
    # no pickle file; fresh start
    state = [0, 0] 
    q = HotQueue(home)
    qf = HotQueue(home + "_sources")
    q.clear()
    qf.clear()
    if args.generic:
        generic = True
        P = GenericParser(name=home,save=False)

if args.vbulletin:
    vbulletin = True
    P = vBulletinParser()

init_logger()


temp = urlparse.urljoin("http:////", home)
archive_link = urlparse.urljoin(temp, "/archive/index.php")
atexit.register(save_state)

num = int(args.num)
init_workers(num)
