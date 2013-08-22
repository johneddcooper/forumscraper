#!/usr/bin/env python
import re
import os
import sys
import signal
import atexit
from time import sleep
import urlparse
import subprocess
from collections import Counter, defaultdict
import pdb
import multiprocessing
from multiprocessing import Value
import logging
import cPickle
import argparse

import MySQLdb as mdb

from BeautifulSoup import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from redis import Redis
from hotqueue import HotQueue

from parsers import *
from local_settings import *
import dblib

def parse_auth_file(filename)

     auth_file = open(filename, "r")
     auth = dict()
     for line in auth_file:
          if line[0] == "#": continue
          line = line.split(',')
          home = line[0]
          auth[home] = {'auth_page': line[1], 'username': line[2], 'password': line[3]}


