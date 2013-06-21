"""Module for handling images from the internet"""

from BeautifulSoup import BeautifulSoup as bs
import re, urlparse, os
from urllib2 import Request, urlopen, URLError, HTTPError
from dblib import *
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def shellquotes(s):
    """Properly escapes paths to avoid problems with the os

    INPUT: string
    RETURNS: string"""
    return "'" + s.replace("'", "'\\''") + "'"

def create_image_dir(dirname):
    """Creates a directory to store images if it does not already exist
    
    INPUT: string (name of the directory)
    RETURNS: path to the image directory"""
    home = os.curdir
    image_dir = os.path.join(home, dirname)
    if not os.path.exists(image_dir): os.mkdir(image_dir)
    return image_dir

def get_thread_dir(post, image_dir):
    """creates a directory tree if it does not already exist to a directory that will contain a thread's images

    INPUT: Post object, string (path to image directory)
    RETURNS: string (path to thread directory)"""
    # search for middle part of a full url
    # E.G. www.foobar.org -> foobar
    s_obj = re.search(r'.+?\.(.+)\..+', post.home)
    if s_obj: 
        forum_name = s_obj.groups(1)[0]
        #print forum_name
    else: 
        forum_name = post.home.lstrip("http://")
        forum_name = forum_name.rstrip("/")
    forum_name = shellquotes(forum_name)

    f_dir = os.path.join(image_dir, forum_name)
    if not os.path.exists(f_dir): os.mkdir(f_dir)

    s_dir = os.path.join(f_dir, shellquotes(post.subname))
    if not os.path.exists(s_dir): os.mkdir(s_dir)

    t_dir = os.path.join(s_dir, shellquotes(post.thread))
    if not os.path.exists(t_dir): os.mkdir(t_dir)

    return t_dir

def get_user_image(user_id, image_dir, src):
    """Downloads a user's avatar

    INPUT: int (user id), string (path to image directory), string (image url)
    RETURNS: None"""
    if not src: return
    user_dir = os.path.join(image_dir, "users")
    if not os.path.exists(user_dir): os.mkdir(user_dir)

    pic_path = os.path.join(user_dir, str(user_id) + ".jpg")
    if os.path.exists(pic_path): return

    download_image(pic_path, 'b', src)
    return


def get_post_images(post, image_dir, msg_image_src, cur):
    """Downloads the images associated with a given post

    INPUT: Post object, string (image directory), list (of image urls), MySQLdb Cursor
    RETURNS: None"""
    print "IN GET POST IMAGES"
    print msg_image_src
    if not msg_image_src: return
    thread_dir = get_thread_dir(post, image_dir)
    for image in msg_image_src:
        image_id = get_id(cur, "IMAGES", "image_src", image)
        if not image_id:
            logger.error("No image id")
            print "NO IMAGE ID"
            continue
        print "DOWNLOADING POST IMAGE"
        logger.info("downloading post image")
        pic_path = os.path.join(thread_dir, str(image_id) + ".jpg")
        if os.path.exists(pic_path): continue
        
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
        if userpic and src: return src[0]
        else: return src
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
        f = urlopen(req)
        print "downloading " + url
        logger.info("downloading %s", url)
        
        # Open our local file for writing
        local_file = open(file_name, "w" + file_mode)
        #Write to our local file
        local_file.write(f.read())
        local_file.close()

        print "DONE DOWNLOADING"
        
    #handle errors
    except HTTPError, e:
        print "HTTP Error:",e.code , url
        logger.error("HTTP Error: %s %s",e.code , url)
    except URLError, e:
        print "URL Error:",e.reason , url
        logger.error("URL Error: %s %s",e.reason , url)

