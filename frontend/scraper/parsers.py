"""This file parses vbulletin forums"""

import re
import logging
import imaget
import sys
from math import sqrt
import argparse
import itertools
import operator
import pprint

import BeautifulSoup
from BeautifulSoup import BeautifulSoup as bs

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


date_marker = ["<!-- status icon and date -->", "<!-- / status icon and date -->"]
message_marker = ["<!-- message -->", "<!-- / message -->"]
sig_marker = ["<!-- sig -->", "<!-- / sig -->"]
edit_marker = ["<!-- edit note -->", "<!-- / edit note -->"]

class Parser():
    def __init__(self):
        return

    def parse(self, src):
        raise NotImplementedError("Necessary method for all parsers")

class ArchiveParser(Parser):
    def __init__(self):
        return
    def parse(self, src):
        b = bs(src)
        posts = b.findAll('div', attrs={'class':'post'})
        if not posts:
            print "Error: No posts" 
            raise
        i = 0
        post_list = []
        while i < len(posts):
            p = posts[i]
            raw_auth = p.find('div', attrs={'class':'author'})
            if not raw_auth or not raw_auth.text:
                print "Error: No author on post %d" % (i)
                continue
            auth = raw_auth.text.encode('utf8')
            raw_auth_link = raw_auth.find('a')
            if raw_auth_link and raw_auth_link.has_key('href'):
                auth_link = raw_auth_link['href'].encode('utf8')
                auth_id = re.findall(re_uid, auth_link)[0]
            else:
                auth_link = ""
                auth_id = ""
            raw_dateline = p.find('div', attrs={'class':'dateline'})
            if not raw_dateline or not raw_dateline.text:
                print "Error: No dateline on post %d" % (i)
                continue
            dateline = raw_dateline.text.encode('utf8')

            message = p.find('div', attrs={'class':'message'})
            if not message:
                print "Error: No message on post %d" % (i)
                continue 
            #imgs = message.findAll("img")
            #img_links = []
            #for j, img in enumerate(imgs):
            #   try:
            #       img_links.append(img['src'])
            #   except:
            #       print "Error: Image %d from post %d on page %d has no source" % (j, i, i_tpage)
            #       #dbp = dblib.post(
            
            #post_id, user_id = dblib.insert_data(con, cur, dbp)
            ddict = defaultdict(str)
            ddict.update({'date': dateline, 'message': message, 'edit': '', 'message images': '', 'user': auth, 'link':''})
            post_list.append(ddict)
            i+=1


class vBulletinParser(Parser):
    def __init__(self):
        return
    """The following two methods are unused in the scraper. The scraper uses the
    archives to traverse the forum. If necessary, the following methods can be used
    to traverse vbulletin forums without archives (if they aren't too heavily modded).
    """
    def get_subforums(self, main_soup):
        subforums = main_soup.findAll('td', attrs={'class':'alt1Active'})
        sublinks = []
        for s in subforums:
            links = s.findAll('a')
            for a in links:
                if not "http" in a['href']:
                    break
            link = a['href']
            text = a.getText()
            sublinks.append({'name':text, 'link':link})

        return sublinks


    def get_threads(self, subforum_soup):
        """This function gets information on the threads from the subforum page. It also returns the total number of pages"""
        threads = subforum_soup.findAll('a',  attrs={'id':lambda x:x and x.startswith('thread_title')}) #pulls out the thread links

        #page _ of _
        page = 1
        page_count = subforum_soup.find('td', attrs={'class':'vbmenu_control'})
        if page_count:
            page_count = page_count.getText()
            page_match = re.search(r'(\d+) .+? (\d+)', page_count)
            if page_match:
                page_count = int(page_match.group(2))
                page = int(page_match.group(1))
                logger.debug("get_threads: page_count = %d, page = %d" % (page_count, page))
            else:
                page_count = 1
                page = 1

        thread_counts = subforum_soup.findAll('td', attrs={'class':'alt2', 'title':lambda x:x and re.match(r'.+?: \d+?', x)})
        if len(threads) != len(thread_counts):
            logger.error('get_threads: thread-count mismatch. Threads = %d; thread_counts = %d' % (len(threads), len(thread_counts)))
            logger.debug('get_threads: threads = %s' % str(threads))
        logger.debug('get_threads: thread_counts = %s' % str(thread_counts))
        threadlinks = []
        for i in range(min(len(threads), len(thread_counts))):
            t = threads[i]
            c = thread_counts[i]
            sanitized = c['title'].replace(',', '')
            count = int(re.search(r'.+?: (\d+?) .+?: (\d+?)',sanitized).group(1)) + 1
            text = t.getText()
            link = t['href']
            threadlinks.append({'name':text, 'link':link, 'count':count})
        return threadlinks, (page, page_count)

    def parse(self, src):

        page_soup = bs(src)
        """
        #page _ of _
        page_count = page_soup.find('td', attrs={'class':'vbmenu_control'})
        if page_count:
            page_count = page_count.getText()
            page_match = re.search(r'(\d+) .+? (\d+)', page_count)
            if page_match:
                page_count = int(page_match.group(2))
                page = int(page_match.group(1))
            else:
                page_count = 1
                page = 1
        """
        posts = page_soup.findAll('table', attrs={'id':lambda x: x and re.match(r'post', x)})
        logging.info('get_post: got %d posts' % len(posts))
        post_list = []
        for p in posts:
            post_link = p.find('a', attrs={'name': lambda x: x and re.match(r'\d+', x)})['href']
            post_string = str(p)
            raw_message = extract(post_string, message_marker[0], message_marker[1])

            date = extract(post_string, date_marker[0], date_marker[1])
            date = strip_tags(date).strip()
            message = self.get_message(raw_message)
            sig = extract(post_string, sig_marker[0], sig_marker[1])
            edit = extract(post_string, edit_marker[0], edit_marker[1])

            msg_image_srcs = imaget.get_image_src(raw_message)
            if msg_image_srcs: msg_image_srcs = msg_image_srcs[0]
            print "message source: " 
            print msg_image_srcs
            print "\n\n\n"

            user = self.get_user(post_string, sig)
            ddict = defaultdict(str)
            ddict.update( dict(
                { 'date': date, 'message': message,
                    'edit': edit, 'images': msg_image_srcs,
                    'plink': post_link
                }.items() + user.items()))
            post_list.append(ddict)
        return post_list



    def get_user(self, post_string, sig = ""):

        user_tag = bs(post_string).find('td', attrs={'class':'alt2'})
        user_name = user_tag.find('a', attrs={'class':'bigusername'}).getText()
        user_link = user_tag.find('a', attrs={'class':'bigusername'})['href']
        user_title = user_tag.findAll('div')[1].getText()
        
        user_div = user_tag.findAll('div')
        inner_ind = 2
        while len(user_div[inner_ind].findAll('div'))<3:
            inner_ind+=1
        inner_name_soup = user_div[inner_ind].findAll('div')
        join_date = inner_name_soup[0].getText()[len("Join Date: "):]

        user_image_src = imaget.get_image_src(user_tag, 1)

        return {'tag': user_tag, 'name':user_name, 'ulink': user_link, 'utitle': user_title, 'join': join_date, 'sig': sig, 'image': user_image_src}

        
        

    def get_message(self, message_str):
        message_soup = bs(message_str)
        images = message_soup.findAll('img')
        for item in images:
          item.extract()
        scripts = message_soup.findAll('script')
        for item in scripts:
          item.extract()
        return str(message_soup)
    

    def extract(self, string, start_marker, end_marker):
      """wrapper function for slicing into a string"""
      start_loc = string.find(start_marker)
      end_loc = string.find(end_marker)
      if start_loc == -1 or end_loc == -1:
        return ""
      return string[start_loc+len(start_marker):end_loc]

    def strip_tags(self, source):
        return re.sub(r'<.+?>', '', source)

class GenericParser:
    """
    Note on data structures.
    What do the functions accept as arguments?

    soup: BeautifulSoup.Soup object
        E.g. soup = bs(src)

    L: list of BeautifulSoup.Tag objects. This is a one dimensional array
        E.g. [<html>...</html>, <head>...</head>, <body>...</body>, etc.]
        L = soup()

    tag: BeautifulSoup.Tag object

    na (name-attribute): a string generated by a call to name_attr(tag).
        It is a concatenation of a tag's name and attribute contents,
        with the special property that all strings of numbers are replaced
        by a single x. This is to match elements such as different posts,
        across their different IDs.

        For example, <div name="post_3421" border=1px> becomes "div-post_x-xpx"
        and has the same name-attr as any other div post with a border.

        The names of the attributes ("name", "border") are dropped.

    D: Dictionary of {name-attributes: counts} within a given L. Thus all of the
        <div name="post_x"> (where x is a number) tags become clustered
        and counted as one. This is used in internal functions to determine which
        tags are systematically generated, as they would tend to appear
        extremely frequently compared to other tags at the same depth level across
        pages.

    tbd: Tags by depth. A list of lists of tags, where the index is the corresponding depth.
        tbd[0] is the highest tag, tbd[1] contain its immediate children, and so forth.
        Returned by a call to get_tags_by_depth(soup)

    dbfs: Depth by files. A list of tbds. dbfs[page][depth][tag]

    fbds: Files by depth. zip(*dbfs). fbds[depth][page][tag]. This allows for easy
        access to a large number of tags per given depth.

    page: The final data structure that contains all the useful extracted tags per
        page. It is still in progress, but in theory, the index should correspond
        to page[post][element], where element corresponds to the exact same element
        across posts (so all page[_][0] might contain "Post Date", or something).

        However, as it stands, there is an extra useless dimension to this array,
        so it looks like page[post][element_chunk][element], and element_chunk
        is always just length 1 and only contains element. That's a bug.

    """
    #############################
    #       Public methods      #
    #############################
    
    def __init__(self, name="Scraper", src=None, save=None, min_soups=5):
        self.name = name
        self.min_soups = min_soups
        if save:
            self.ready = True
            self.training = False 
            self.load(save)
        elif src:
            self.sources = []
            self.ready = False
            self.training = False 
            self.add_source(src)
        else:
            self.sources = []
            self.ready = False
            self.training = False 
    def add_source(self, src):
        """Add source to parser. Once enough have been gathered, runs train()"""
        self.sources.append(src)
        if len(self.sources) >= self.min_soups:
            self.train()
            return map(self.parse, self.sources)
        return None

    def is_ready(self):
        return self.ready
    
    def is_training(self):
        return self.training

    def load(self, save):
        self.labels, self.clusters, self.use_text, \
            self.depth, self.outliar_names = pickle.load(open(save))
    
    def parse(self, src):
        if len(self.sources) < self.min_soups:
            self.add_source(src)
            return
        soup = bs(src)
        contents = self.extract_content(soup)
        cd = self.label_contents(contents)
        return cd
    
    ##################################
    #       Internal functions       #
    ##################################

    def train(self):
        """Train over list of soups to find location/names of relevant tags"""
        if len(self.sources) < self.min_soups:
            print "Not enough training data. Add more before training."
            raise
        soups = map(bs, self.sources)
        dbfs = map(self.get_tags_by_depth, soups)
        # dbfs = Depth by files [f1:[d1, d2, ...], f2:[d1, d2, ...],...]
        # f_i and f_j can be different lengths, depending on their max depth
        # len(dbfs) is always the number of pages

        fbds = zip(*dbfs)
        # fbds = Files by depth [d1:[f1, f2, ...], d2[f1, f2, ...], ...]
        # all d_i are the same length, because they all contain equal # files
        # each f_i entry is actually a BeautifulSoup tag, so fbds[0][0] might contain
        # "[<HTML>...</HTML>]", for example.
        # len(dbfs) is the maximum tag depth of all the pages.

        if len(fbds) < 3:
            print "Min depth not achieved."
            sys.exit()
        #print "Beginning comparison at depth level", len(fbds)/3

        for i in xrange(len(fbds)/3, len(fbds)-1):
            if not all(self.same_tags(x1, x2) for x1 in fbds[i] for x2 in fbds[i]):
                #print "Not all tags at depth level %d are the same"%i
                break
        self.depth = i
        if self.depth==len(fbds)-1:
            print "Unusually homogenous webpage. You may continue, at your own risk."
            
        for i in xrange(len(fbds)):
            fbds[i] = [item for sublist in fbds[i] for item in sublist]
        
        outliars = self.get_outliars_from_dict(
                    self.tag_distribution(fbds[self.depth])
                                            )
        self.outliar_names = outliars 
        contents = self.parse(soups[0])
        self.labels, self.clusters, self.use_text = self.get_labels(contents)
        pickle.dump(
            [self.labels, self.clusters, self.use_text, \
             self.depth,  self.outliar_names         ], \
             open("%s.p"%self.name, "w"))
   
    def get_labels(self, contents):
        """Query user to label data.
        """
        labels = {}
        clusters = {}
        use_text = {}
        for i,c in enumerate(contents):
            pprint.pprint(c)
            prompt = """Label this data:
            [dD] discard
            0) username
            1) user title 
            2) message 
            3) post date
            4) join date 
            5) signature
            6) edits
            - other: type in label
            """
            label = raw_input("Label ((D) discard): ").lower().strip()
            na = self.name_attr(c[0])
            try:
                num = int(label)
                if num == 0:
                    label = 'user'
                elif num == 1:
                    label = 'utitle'
                elif num == 2:
                    label = 'msg'
                elif num == 3:
                    label = 'date'
                elif num == 4:
                    label = 'joindate'
                elif num == 6:
                    label = 'sig'
                elif num == 7:
                    label = 'edits'
                if na in labels.keys():
                    labels[na].append(label)
                else:
                    labels[na] = [label]
                for elem in c:
                    print elem.text
                text = raw_input("Store text instead of raw tags? (y/[n]) ").lower().strip()
            except:
                if label == 'd':
                    label = "d%d"%i
                else:
                    labels[na].append(label)
                    for elem in c:
                        print elem.text
                    text = raw_input("Store text instead of raw tags? (y/[n]) ").lower().strip()
            stats = self.calc_stats(c)
            clusters[stats] = label
            print "----------"
        return labels, clusters, use_text
    
    def extract_content(self, soup):
        """Extracts content of a soup, given training data"""
        if not self.depth:
            print "Error: Need to train data first."
            return
        tbd = self.get_tags_by_depth(soup)
        tags = [self.get_tags_by_string(out, tbd[self.depth]) for out in self.outliar_names]
        contents = self.extract_contents(tags)
        return contents 
    
    def label_contents(self, contents):
        content_dict = defaultdict(str) 
        for c in contents:
            na = self.name_attr(c[0])
            if na not in self.labels.keys():
                print "%s has not appeared in training data." % na
            else:
                # candidate labels
                clabels = self.labels[na]
                if len(clabels)==1:
                    content_dict[clabels[0]] = c
                else:
                    cands = {k: v for (k, v) in self.clusters.items() if v in clabels}
                    stat = self.calc_stats(c)
                    
                    calc_ratio = lambda x, y: max(difflib.SequenceMatcher(str(z), str(y)).ratio() for z in x)
                    min_ratio = 0
                    min_label = ""
                    for k in cands.keys():
                        ratio = calc_ratio(c, k)
                        print "Ratio between %s and %s: %f" % (na, k, ratio)
                        if ratio < min_ratio:
                            min_ratio = ratio
                            min_label = cands[k]
                    content_dict[cands[k]] = c

        self.ready = True
        self.training = False
        return content_dict
   

    def get_tags_by_depth(self, soup):
        """get_tags_by_depth(soup)
        Takes a BeautifulSoup object. Returns a list [d0, d1, ..., dn],
        where d_i is a list of the BeautifulSoup.Tag objects at that given depth level.
        For example:
        d0=[<head>..</head>, <body>..</body>]
        d1=[<meta>.., <table>.., <script>..]

        """
        c = soup(recursive=False)
        if not c:
            return []
        tags_by_depth = [[t for t in c]]
        d = 1
        while True:
            tags = []
            for t in tags_by_depth[d-1]:
                tags.extend(t.findChildren(recursive=False))
        
            tags = filter(None, tags)
            if tags:
                tags_by_depth.append(tags)
            else:
                break

            d+=1
        return tags_by_depth

    def same_tags(self, L1, L2):
        """same_tags(L1, L2)
        L1 and L2 are lists of BeautifulSoup.Tag objects
        Returns True iff all tags in one list are in the other.
        
        """ 
        
        s1 = set(self.tag_distribution(L1).keys())
        s2 = set(self.tag_distribution(L2).keys())

        return all(k1 in s2 for k1 in s1) and \
                all(k2 in s1 for k2 in s2)


    def name_attr(self, tag, strip_nums=1, strip_orphans=0, strip_links=0):
        """name_attr(tag, strip_nums=1, strip_orphans=0, strip_links=1)
        Takes a BeautifulSoup.Tag object.
        Returns a string formatted "name-first_attribute-second_attribute".
        E.g. [<div class="post" style="font-weight:normal"></div>] returns "div-post-font-weight:normal"
        
        strip_nums: strips the numbers from the attribute, replacing any series of them with a single "x"
        E.g. [<div class=post232></div>] returns "div-postx"

        strip_orphans: returns an empty string for any tag that doesn't have attributes.
        
        strip_links: returns an empty string for any link tags.
        
        """
        if not tag:
            return ""
        if not strip_links or tag.name!= 'a':
            if tag.attrs:
                at = [tag.attrs[i][1] for i in xrange(len(tag.attrs))]
                at = "-".join(at)
                if strip_nums:
                    at = re.sub(r"\d+","x", at)
                return "%s-%s"%(tag.name, at)
            elif not strip_orphans:
                return tag.name
        return ""

    def get_tags_by_string(self, na, L):
        """get_tags_by_string(string, list of BeautifulSoup.Tag objects)
        Takes a name-attr string (as returned by name_attr()) and returns tags that match

        """
        
        return filter(lambda x: self.name_attr(x)==na, L)

    def tag_distribution(self, L, strip_links=0, strip_nums=1, strip_orphans=1):
        """tag_distribution(L, strip_links=1, strip_nums=1, strip_orphans=1):
        L is a list of BeautifulSoup.Tag objects
        Uses tag name and attributes to generate a dictionary of counts.

        E.g. [BeautifulSoup("<div class=post32124></div>")] returns {'div-postx': 1}

        """
        ud = {}
        for x in L:
            n = self.name_attr(x, strip_nums=strip_nums, strip_links=strip_links,strip_orphans=strip_orphans)
            if n:
                if n in ud.keys():
                    ud[n] += 1
                else:
                    ud[n] = 1
        return ud


    def get_outliars_from_dict(self, D):
        """get_outliars_from_dict(tag_dictionary)
        Internal function for outliars()
        Takes a dictionary where the values are integer counts.
        Returns a list of the keys where the values are two standard deviations above the mean.
        """
        m = mean(D.values())
        s = std(D.values())
        k = filter(lambda x: x[1] > m + 2*s, D.items())
        if k:
            return zip(*k)[0]

    def outliars(self, tbd, d):
        """outliars(tags_by_depth, depth)
        Returns all tags that appear disproportionately often at the given depth.

        """

        outliars = self.get_outliars_from_dict(self.tag_distribution(tbd[d]))
        if not outliars:
            return []
        out_tags = (self.get_tags_by_string(x, tbd[d]) for x in outliars)
       
        out_tags_no_boring = []
        for i, x in enumerate(out_tags):
            if any(not e.text for e in x):
                continue
            if all(e.text==x[0].text for e in x):
                continue
            out_tags_no_boring.append(x)

        return out_tags_no_boring

    def is_boring(self, tag):
        """Returns true if tag
        - has no text
        - is not an image
        - does not contain an image
        - is not a script tag
        """
        if tag.name == "script":
            return True
        if len(tag.text) == 0 and not tag.first('img', src=True)\
                                and tag.name != 'img':
            return True
        return False

    def extract_boring_tag(self, tag):
        """extract_boring_tag(tag)
        Takes a tag
        Calls extract() on its children if they are boring, (see method is_boring())
        Extracts and returns True if the tag itself fits the same criteria

        """
        for comment in tag.findChildren(text=lambda txt:
                            isinstance(txt, BeautifulSoup.Comment)
        ):
            comment.extract()
        
        for child in tag.findChildren():
            if self.is_boring(child):
                child.extract()
        
        if self.is_boring(tag):
            tag.extract()
            return True
        return False
    """
    def recur_extract(self, tag):
        if self.is_boring(tag):
            return
        cs = tag(recursive=False)
        if len(cs) == 0:
            if tag.name == 'img':
                data = [tag.get('src')]
            else:
                data = [tag.getText()]
            tag.extract()
        else:
            data = []
            for c in cs:
                data.extend(recur_extract(c))
            filter(None, data)
            if tag.getText():
                data.extend([tag.getText()])
        return data
    """
    def extract_contents(self, page):
        """extract_contents(outnames, page, depth)
        this takes each post, which consists of several large and nested
        div/tables, and extracts the subcontents that are identical across posts
        
        """

        newt = []
        posts = []
        for item in page:
            children = [tag() for tag in item] 
            
            cbd = map(self.get_tags_by_depth, item)
            dbc = zip(*cbd)

            dbc_names = [[[self.name_attr(x) for x in msg if not self.is_boring(x)] for msg in dep] for dep in dbc] 
            
            tags = []
            tagged = []
            for i in xrange(len(dbc_names)-1, -1, -1):
                depth = dbc_names[i]
                for entry in depth:
                    for name in entry:
                        if name and name not in tagged:
                            if all(name in other_entries for other_entries in depth):
                                tagged.append(name)
                                tag = [self.get_tags_by_string(name, entries) for entries in dbc[i]]
                                ts = zip(*tag)
                                for t in ts:
                                    
                                    map(self.extract_boring_tag, t)
                                    map(lambda x: x.extract(), t)
                                    if self.is_boring(t[0]):
                                        continue
                                    if all(t[0] == x for x in t):
                                        continue
                                    tags.append(t)
            if tags:
                posts.extend(tags)
        return posts

    def pn(L):
        """Print name: Calls name_attr() on all elements in list of BeautifulSoup.Tag objects."""
        return filter(None, map(self.name_attr, L))

    def calc_stats(self, tags):
        """Calculates certain metrics for clustering tags.
        """
        count = lambda x, y: len(filter(lambda x1: x1 in y, x))
        avglen = self.mean(map(len, map(str,tags)))
        numdig = self.mean(map(lambda x: count(x, string.digits), map(lambda x: x.getText(), tags)))
        numupper = self.mean(map(lambda x: count(x, string.ascii_uppercase), map(lambda x: x.getText(), tags)))
        numwhite = self.mean(map(lambda x: count(x, string.whitespace), map(lambda x: x.getText(), tags)))
        return numdig/avglen, numupper/avglen, numwhite/avglen

    ##################################
    # Miscellanious numeric functions#
    ##################################

    def mean(self, li):
        """returns mean of a list"""

        return float(sum(li))/len(li)

    def std(self, li):
        """returns standard deviation of a list"""

        m = mean(li)
        return sqrt(mean([abs(x-m) for x in li]))

"""
def of(name, num, suffix=""):
    soups = []
    for i in xrange(1, int(num)+1):
        soups.append(bs(open("%s%s%s"%(name,str(i),suffix)).read()))
    return soups

if len(sys.argv) < 4:
    print "usage:"
    sys.exit()

soups = of(sys.argv[1], sys.argv[2], sys.argv[3])
if len(sys.argv) > 4:
    save = sys.argv[4]
    S = Scraper(save=save)
else:
    S = Scraper(soups=soups[:-1])

scrape= S.scrape(soups[-1])

"""

