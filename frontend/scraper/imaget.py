"""Module for handling images from the internet"""

from BeautifulSoup import BeautifulSoup as bs
import re, urlparse, os, sys
from urllib2 import Request, urlopen, URLError, HTTPError
from dblib import *
import logging
import imghdr
import glob
import pdb
import socket

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

image_dir = ""

def shellquotes(s):
    """Properly escapes paths to avoid problems with the os

    INPUT: string
    RETURNS: string"""
    return "'" + s.replace("'", "'\\''") + "'"

def create_image_dir(dirname = "images"):
    """Creates a directory to store images if it does not already exist
    
    INPUT: string (name of the directory)
    RETURNS: path to the image directory"""
    global image_dir
    home = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))
    parent = os.path.abspath(os.path.join(home, ".."))
    dirs = ['users', 'threads']

    image_dir = os.path.join(parent, dirname)
    if not os.path.exists(image_dir): os.mkdir(image_dir)

    for D in dirs:
        path = os.path.join(image_dir, D)
        if not os.path.exists(path): os.mkdir(path)


    return image_dir

def get_forum_name(home):
    # search for middle part of a full url
    # E.G. www.foobar.org -> foobar
    s_obj = re.search(r'.+?\.(.+)\..+', home)
    if s_obj: 
        forum_name = s_obj.groups(1)[0]
        #print forum_name
    else: 
        forum_name = post.home.lstrip("http://")
        forum_name = forum_name.rstrip("/")
    return forum_name

def get_thread_dir(post):
    """creates a directory tree if it does not already exist to a directory that will contain a thread's images

    INPUT: Post object, string (path to image directory)
    RETURNS: string (path to thread directory)"""
    """forum_name = shellquotes(get_forum_name(post.home))

    f_dir = os.path.join(image_dir, forum_name)
    if not os.path.exists(f_dir): os.mkdir(f_dir)

    s_dir = os.path.join(f_dir, shellquotes(post.subname))
    if not os.path.exists(s_dir): os.mkdir(s_dir)

    t_dir = os.path.join(s_dir, shellquotes(post.thread))
    if not os.path.exists(t_dir): os.mkdir(t_dir)


    threads = os.path.join(f_dir, "threads")
    if not os.path.exists(threads): os.mkdir(threads)

    print post.thread_id
    """
    t_dir = os.path.join(image_dir, "threads", str(post.thread_id))
    if not os.path.exists(t_dir): os.mkdir(t_dir)

    return t_dir

def get_image_dir(cur, image_id, full_path=False):

    image_id = int(image_id)
    post_id  = get_item(cur, "IMAGES",  "post_id", "image_id", image_id)
    if post_id:
        thread_id = get_item(cur, "POSTS", "thread_id", "post_id", post_id)
        if not thread_id: return None
        thread_name = get_item(cur, "THREADS", "thread_name", "thread_id", thread_id)
        subforum_id = get_item(cur, "THREADS", "subforum_id", "thread_id", thread_id)
        if not subforum_id: return None
        subforum_name = get_item(cur, "SUBFORUMS", "subforum_name", "subforum_id", subforum_id)
        forum_id  = get_item(cur, "SUBFORUMS", "forum_id", "subforum_id", subforum_id)
        if not forum_id: return None
        forum_name = get_item(cur, "FORUMS", "forum_name", "forum_id", forum_id)

        i_dir = os.path.join(image_dir, shellquotes(forum_name), shellquotes(subforum_name), shellquotes(thread_name))
        if not full_path: return i_dir
        else: return os.path.join(i_dir, image_id + ".jpg")

    else:
        user_id = get_item(cur, "IMAGES", "user_id", "image_id", image_id)
        if not user_id: return None
        user_dir = os.path.join(image_dir, "users")
        if not full_path: return user_dir
        else: return os.path.join(user_dir, user_id + ".jpg")
        

def get_user_image(user_id, src):
    """Downloads a user's avatar

    INPUT: int (user id), string (path to image directory), string (image url)
    RETURNS: None"""
    if not src: return
    user_dir = os.path.join(image_dir, "users")
    if not os.path.exists(user_dir): os.mkdir(user_dir)

    pic_path = os.path.join(user_dir, str(user_id) + ".")
    if os.path.exists(pic_path): return

    download_image(pic_path, 'b', src)
    return


def get_post_images(post, msg_image_src, cur):
    """Downloads the images associated with a given post

    INPUT: Post object, string (image directory), list (of image urls), MySQLdb Cursor
    RETURNS: None"""
    print "IN GET POST IMAGES"
    print msg_image_src
    if not msg_image_src: return
    thread_dir = get_thread_dir(post)
    for image in msg_image_src:
        image_id = get_id(cur, "IMAGES", "image_src", image)
        if not image_id:
            logger.error("No image id")
            print "NO IMAGE ID"
            continue
        print "DOWNLOADING POST IMAGE"
        logger.info("downloading post image")
        pic_path = os.path.join(thread_dir, str(image_id) + ".*")
        if glob.glob(pic_path): continue
        pic_path = os.path.join(thread_dir, str(image_id) + ".")
        
        if image.find("http") == -1: image = post.home + image
        download_image(pic_path, 'b', image)
    return

def get_image_src(tag, userpic = 0):
    """Extracts an image url from a block of text

    INPUT: string OR BeautifulSoup Tag (html source), boolean (is the picture a user's avatar?)
    RETURNS: None, string, or list of strings"""
    soup = bs(str(tag))
    html = soup.findAll('img')
    src = []
    if html:
        for item in html:
            # User's avatar's are gotten through a php request.
            # post images may or may not be (usually not) hosted on the site
            if (item['src'].find('php') != -1 and userpic) or (not userpic):
              src.append(item['src'])
              if not userpic: print "FOUND IMAGE: " + item['src']
              item.extract()
        if userpic and src: return src[0]
        elif src: return src, soup.prettify()
        else: return None
    else:
        return None

def download_image(file_name, file_mode, url):
    """Dowloads an image to a given file

    INPUT: string (path to be downloaded to), string (binary or text modes), string (image url)
    RETURNS: None"""
    #create the url and the request
    req = Request(url)
    
    # Open the url
    try:
        f = urlopen(req, None, 5)
        print "downloading " + url
        logger.info("downloading %s", url)
        
        image = f.read()
        # Open our local file for writing
        header = imghdr.what('', image)
        if not header: return
        local_file = open(file_name + header, "w" + file_mode)
        #Write to our local file
        local_file.write(image)
        local_file.close()

        print "DONE DOWNLOADING"
        
    #handle errors
    except HTTPError, e:
        print "HTTP Error:",e.code , url
        logger.error("HTTP Error: %s %s",e.code , url)
    except URLError, e:
        print "URL Error:",e.reason , url
        logger.error("URL Error: %s %s",e.reason , url)
    except socket.error, e:
        print "Socket Error:" + str(sys.exc_info()) + url
        logger.error("Socket Error: %s %s",str(sys.exc_info()), url)
    except Exception, e:
	print "Unknown  error: %s" % str(sys.exc_info())
	logger.error("Unknown  error: %s", str(sys.exc_info()))

