shell:
	mysql -u root -p forumsdb

db:
	mysql -u root -p < create.sql
	python2.7 db_utf8.py
	rm -rf images

watchdog:
	python2.7 frontend/scraper/watchdog.py http://www.gofuckbiz.com/ 0

run:
	python2.7 frontend/scraper/vbscraper.py http://www.gofuckbiz.com/ 0

mybb:
	python2.7 frontend/scraper/vbscraper.py http://www.hackforums.net/

clean:
	rm -rf *.pyc

server:
	python2 frontend/manage.py runserver
