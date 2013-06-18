required packages:
sudo apt-get install mysql-server
sudo apt-get install python-mysqldb
sudo apt-get install python-pip
sudo pip install selenium
sudo pip install BeautifulSoup
sudo apt-get install xautomation

usage:
to create database, run
  mysql -u 'mysql_username' < create.sql

copy the settings file, then edit it to contain the correct login credentials
  cp local_settings.py.sample local_settings.py

then run
  python db_utf8.py
(changes mysql table columns to all accept UTF-8)

finally, run
  python vbscraper.py URL

URL must contain http and end with a /
good: http://forum.doom9.org/
bad : forum.doom9.org

THE BROWSER MUST REMAIN IN FOCUS TO INTERRUPT HUNG PAGES!

Todo:
#####

-Restarts
	-Restarts work, but the implementation does not allow for multiple instances to run on the same DB

=============================================================================================================================

-Fix bugs with watchdog
	-Sometimes hangs (Especially on runtime errors of the subprocess)
		-blocking on read from stderr. May be fixed by making signal handlers or finding a way to cancel a read or break the pipe
			-Or maybe by using unix sockets (LAST RESORT
	-Exit Gracefully (Close browser window on SIG_KILL)

=============================================================================================================================

-Format database
	-DB normalized, but ForiegnKeys are not implemented
	-Add table for images

=============================================================================================================================

-Make code nicer
	-Add more comments
	-Create docstrings to compile documentation
	-Compile into a python package?
	-Modularize the VBulletin code

=============================================================================================================================

-Add arguments
	-Arg for multiple sites and/or subprocesses
	-Read input from file

=============================================================================================================================

-Download images
	-create directory structure for images
	-link image location to the DB (forum, thread, user, post)
	don't download user images more than once

=============================================================================================================================

-Other forum packages (phpbb, invision power board, simple machines)

=============================================================================================================================

-Create web front-end
	-Django looks like the obvious choice.
	-start by recreating the forum structure
