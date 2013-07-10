required packages:
sudo apt-get install mysql-server
sudo apt-get install python-mysqldb
sudo apt-get install python-pip
sudo pip install selenium
sudo pip install BeautifulSoup
sudo apt-get install xautomation

usage:
to create database (THIS PURGES A DB IF IT EXISTS), run
  make db

copy the settings file, then edit it to contain the correct login credentials
  cp local_settings.py.sample local_settings.py

finally, run
  make run (for the standalone scraper)
  make watchdog (to run the scraper with a timeout watchdog)

URL must contain http and end with a /
good: http://forum.doom9.org/
bad : forum.doom9.org

THE BROWSER MUST REMAIN IN FOCUS TO INTERRUPT HUNG PAGES!

Todo:
#####

-Restarts
1)	-Restarts work, but the implementation does not allow for multiple instances to run on the same DB
		- Use Pickle
	-We need a way to know which threads have had posts added to them. Current implementations ignore a thread after
	 scraping it once.

=============================================================================================================================

-Fix bugs with watchdog
	-Exit Gracefully (Close browser window on SIG_KILL)
2)	-Sometimes hangs (Especially on runtime errors of the subprocess)
		-blocking on read from stderr. May be fixed by making signal handlers or finding a way to cancel a read or 
		 break the pipe. Or maybe by using unix sockets (LAST RESORT
		-Timeouts cause the scraper to restart, this does not always resolve the timeout issue. The same webpage
		 is loaded again, trigerring another timeout. This may be resolved by maintaining a count of timeout on
		 pages in the DB.

=============================================================================================================================

-Format database
	-DB normalized, but ForiegnKeys are not implemented
	-Add table for images						#DONE

=============================================================================================================================

-Make code nicer
	-Add more comments						#DONE
	-Create docstrings to compile documentation 			#DONE
	-Compile into a python package		    			#DONE
	-Modularize the VBulletin code

=============================================================================================================================

-Add arguments
	-Arg for multiple sites and/or subprocesses
	-Read input from file

=============================================================================================================================

-Download images
	-create directory structure for images 				#DONE
	-link image location to the DB (forum, thread, user, post) 	#DONE
	-don't download user images more than once 			#DONE
	-Restructire image directory


-Other forum packages (phpbb, invision power board, simple machines)
	-Restructure scraper so that the scraper gets a list of regexes to indentify key parts
=============================================================================================================================

-Create web front-end
	-Django looks like the obvious choice.
	-start by recreating the forum structure 		       #DONE
