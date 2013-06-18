from BeautifulSoup import BeautifulSoup as bs
import re, urlparse, os
from urllib2 import Request, urlopen, URLError, HTTPError
import dblib

def shellquotes(s):
    return "'" + s.replace("'", "'\\''") + "'"

def create_image_dir(dirname):
	home = os.curdir
	image_dir = os.path.join(home, dirname)
	if not os.path.exists(image_dir): os.mkdir(image_dir)
	return image_dir

def get_thread_dir(post, image_dir):
	s_obj = re.search(r'.+?\.(.+)\..+', post.home)
	if s_obj: forum_name = s_obj.groups(1)
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
	if not src: return
	user_dir = os.path.join(image_dir, "users")
	if not os.path.exists(user_dir): os.mkdir(user_dir)

	pic_path = os.path.join(user_dir, str(user_id) + ".jpg")
	if os.path.exists(pic_path): return

	download_image(pic_path, 'b', src)
	return

def get_image_src(tag):
	soup = bs(str(tag))
	html = soup.find('img')
	if html:
		src = html['src']
		return src
	else:
		return None

def download_image(file_name, file_mode, url):
	
	#create the url and the request
	req = Request(url)
	
	# Open the url
	try:
		f = urlopen(req)
		print "downloading " + url
		
		# Open our local file for writing
		local_file = open(file_name, "w" + file_mode)
		#Write to our local file
		local_file.write(f.read())
		local_file.close()

		print "DONE DOWNLOADING"
		
	#handle errors
	except HTTPError, e:
		print "HTTP Error:",e.code , url
	except URLError, e:
		print "URL Error:",e.reason , url

