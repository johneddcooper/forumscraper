shell:
	mysql -u root -p forumsdb

db:
	mysql -u root -p < create.sql
	python2.7 db_utf8.py
	rm -rf images

watchdog:
	python2.7 watchdog.py http://www.gofuckbiz.com/

run:
	python2.7 vbscraper.py http://www.gofuckbiz.com/

clean:
	rm -f *.pyc
