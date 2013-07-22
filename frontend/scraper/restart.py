import sys
import os
import pickle
from time import sleep

threads = {}

def get_state_folder():
    """Creates a directory to store images if it does not already exist
    
    INPUT: string (name of the directory)
    RETURNS: path to the image directory"""
    home = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))
    parent = os.path.abspath(os.path.join(home, ".."))
    pickle_dir = os.path.join(parent, "pickles")
    if not os.path.exists(pickle_dir): os.mkdir(pickle_dir)
    return pickle_dir


def get_pickle_file(forum_id, mode):
    path = os.path.join(get_state_folder(), str(forum_id) + ".p")
    if (mode == 'r'or mode == 'rb') and not os.path.exists(path): return None
    return open(path, mode)

def save_state(forum_id):
    pickle_file = get_pickle_file(forum_id, "w")
    pickle.dump(threads, pickle_file)

def restore_state(forum_id):
    pickle_file = get_pickle_file(forum_id, "r")
    if not pickle_file: return
    threads = pickle.load(pickle_file)

def dump_cookies(forum_id, webdriver):
    pickle_file = get_pickle_file(str(forum_id) + "_cookies", "wb")
    pickle.dump(webdriver.get_cookies(), pickle_file)

def get_cookies(forum_id, webdriver):
    pickle_file = get_pickle_file(str(forum_id) + "_cookies", "rb")
    if not pickle_file: 
        sleep(90)
        return
    cookies = pickle.load(pickle_file)
    for cookie in cookies:
        webdriver.add_cookie(cookie)
