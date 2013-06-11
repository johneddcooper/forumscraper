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

The browser should remain in focus; sometimes the program sends an "Escape" keypress to interrupt a hung page.

Todo:
-Restarts
-Format database
-Make code nicer
-Add arguments

-Other forum packages (phpbb, invision power board, simple machines)
