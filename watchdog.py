import threading
import signal
import subprocess as sub
from subprocess import PIPE
from vbscraper import parse_args
from time import sleep

flag = 1
sc1 = None

class Scraper:

	def __init__(self, args):
		self.event = threading.Event()
		self.args = args
		self.scraper = sub.Popen(args, stderr=PIPE)

	def kill(self):
		retcode = self.scraper.poll()

		if (retcode < 0 or retcode > 0):
			print "Scraper Failed"
		if retcode == 0:
			print "Scraper finished"
		else:
			print "Scraper Running. Terminating now"
			self.scraper.terminate()

	def restart(self):
		self.scraper = sub.Popen(self.args, stderr=PIPE)

def add_scraper(foo):
	Scrapers.append(foo)

def hello():
	print "hello world"

#t = threading.Timer(5.0, hello)
#t.start()

def kill_proc(signum, frame):
	global flag
	global sc1
	if not flag:
	   try:
		print "KILLING PROC"
		sc1.kill()
		sc1.scraper.wait()
		print "Process killed"
		sleep(3)
		print "RESTARTING PROC"
		sc1.restart()
		print "PROC RESTARTED"
		flag = 1
		signal.alarm(30)
	   except OSError:
		print "Error in killing process.\nThe process may have already been killed"
	else:
		flag = 0
		print "IN ALARM HANDLER: TURNING FLAG OFF"
		signal.alarm(30)
	return

def main():

	global flag
	global sc1
	home = parse_args()
	args = ["python2.7", "vbscraper.py", home]
	#t = threading.Timer(5.0, kill_proc)
	#t.start()
	sc1 = Scraper(args)
	signal.signal(signal.SIGALRM, kill_proc)

	#(stdoutdata, stderrdata) = sc1.scraper.communicate()
	while True:
		signal.alarm(30)
		line = sc1.scraper.stderr.read(7)
		if line == "TIMEOUT":
			signal.alarm(5)
			print "TURNING FLAG OFF"
			flag = 0
		elif line == "REFRESH":
			print "TURNING FLAG ON"
			flag = 1
		signal.alarm(45)
		"""
		else:
			signal.alarm(5)
			print "TURNING FLAG OFF"
			flag = 0
		"""
		

if __name__ == "__main__":
	main()
