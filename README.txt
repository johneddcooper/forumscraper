required packages:
sudo apt-get install mysql-server
sudo apt-get install python-mysqldb
sudo apt-get install python-pip
sudo pip install selenium
sudo pip install BeautifulSoup
sudo apt-get install xautomation

usage:
to create database, run
  mysql < create.sql

edit db_utf8.py to contain proper mysql credentials, then run
  python db_utf8.py

to scrape, run
  python vbscraper.py URL

URL must contain http and end with a /
good: http://forum.doom9.org/
bad : forum.doom9.org

Todo:
-Restarts
-Format database
-Make code nicer

-Other forum packages (phpbb, invision power board, simple machines)
