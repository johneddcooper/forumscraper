from BeautifulSoup import BeautifulSoup as bs
import re, urlparse
from urllib2 import Request, urlopen, URLError, HTTPError

def get_image_src(tag):
	soup = bs(str(tag))
	print "SOUP: " + str(soup)
	html = soup.find('img')
	print "HTML: " + str(html)
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
		
	#handle errors
	except HTTPError, e:
		print "HTTP Error:",e.code , url
	except URLError, e:
		print "URL Error:",e.reason , url

