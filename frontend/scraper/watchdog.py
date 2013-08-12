#!/usr/bin/python2
"""This module acts as a wrapper around vbscraper. It watches for timeouts and restarts scraping on hang"""
import threading
import signal
import subprocess as sub
from subprocess import PIPE
from vbscraper import parse_args
from time import sleep
import sys
import os
import argparse

flag = 1
sc1 = None
home_dir = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

class Scraper:
	"""This class contains subprocesses that are the individual scrapers"""

	def __init__(self, args):
		self.event = threading.Event()
		self.args = args
		self.scraper = sub.Popen(args, stderr=PIPE)

	def kill(self):
		retcode = self.scraper.poll()
                print "retcode: " + str(retcode)

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

def parse_args():

    backends = ["mybb", "vbulletin"]

    parser = argparse.ArgumentParser(description="Scrape a webforum")
    parser.add_argument("--threads", "-t", metavar="number of threads", type=int, default=2)
    parser.add_argument("forum", metavar="forum url", type=string)
    parser.add_argument("-b", "--backend", metavar="type of forum", type=string, choices=backends, required=True)


def kill_proc(signum, frame):
	"""Kills a process, then restarts it. SIGALRM signal handler"""
	global flag
	global sc1
        print "in signal handler"
	if not flag:
	   try:
		print "KILLING PROC"
		sc1.kill()
		sc1.scraper.wait()
		print "Process killed"
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
	args = ["python2.7", os.path.join(home_dir, "vbscraper.py"), home, "0"]
        print args
	#t = threading.Timer(5.0, kill_proc)
	#t.start()
	sc1 = Scraper(args)
        print "created scraper"
        print sc1
	signal.signal(signal.SIGALRM, kill_proc)

	#(stdoutdata, stderrdata) = sc1.scraper.communicate()
	print "setting alarm"
	signal.alarm(120)
	while True:
		line = sc1.scraper.stderr.read(7)
		if line == "TIMEOUT":
			signal.alarm(5)
			print "TURNING FLAG OFF"
			flag = 0
		elif line == "REFRESH":
			print "TURNING FLAG ON"
			flag = 1
                elif line == "EXITING":
                        print "DIED, restarting"
                        sc1.restart()
		signal.alarm(30)
		"""
		else:
			signal.alarm(5)
			print "TURNING FLAG OFF"
			flag = 0
		"""
		

if __name__ == "__main__":
	main()
