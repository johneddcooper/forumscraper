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
	-Restarts work, but the implementation does not allow for multiple instances to run on the same DB
		- Use Pickle                                          #DONE

	-We need a way to know which threads have had posts added to them. Current implementations ignore a thread after
	 scraping it once.                                            #DONE

=============================================================================================================================

-Fix bugs with watchdog
	-Exit Gracefully (Close browser window on SIG_KILL)           #DONE
	-Sometimes hangs                                              #DONE
		-blocking on read from stderr. May be fixed by making signal handlers or finding a way to cancel a read or 
		 break the pipe. Or maybe by using unix sockets (LAST RESORT
		-Timeouts cause the scraper to restart, this does not always resolve the timeout issue. The same webpage
		 is loaded again, trigerring another timeout. This may be resolved by maintaining a count of timeout on
		 pages in the DB.

=============================================================================================================================

-Implement better interprocess communication
        -Use poll or select for reading in the watchdog
        -Have the watchdog send data about what threads to scrape by the subprocesses
                -Maybe have the watchdog scrape the forums and subforums first.

=============================================================================================================================

-Set definitive roles for the watchdog and the scrapers.
        -Watchdog
             -Wait for scrapers to die and restart them.
             -Tell scrapers what threads to scrape.
             -Keep track of what threads are done/where they are
             -Save and restore state
        -Scrapers
             -Scrape threads
             -Download post and user info

=============================================================================================================================

-Create a robust argument system

=============================================================================================================================

-Format database
	-DB normalized, but ForiegnKeys are not implemented           #EHHH
	-Add table for images				              #DONE

=============================================================================================================================

-Make code nicer
	-Add more comments					      #DONE
	-Create docstrings to compile documentation 		      #DONE
	-Compile into a python package		    		      #DONE
	-Modularize the VBulletin code                                #DONE

=============================================================================================================================

-Add arguments
	-Arg for multiple sites and/or subprocesses
	-Read input from file

=============================================================================================================================

-Download images
	-create directory structure for images 			      #DONE
	-link image location to the DB (forum, thread, user, post)    #DONE
	-don't download user images more than once 		      #DONE
	-Restructire image directory                                  #DONE


-Other forum packages (phpbb, invision power board, simple machines)
	-Restructure scraper so that the scraper gets a list of
                                      modules to indentify key parts  #DONE
=============================================================================================================================

-Create web front-end
	-Django looks like the obvious choice.                        #DONE
	-start by recreating the forum structure 		      #DONE
        -implement search                                             #DONE
            -create search filters (user, forum, time)
        -implement database direct download link
