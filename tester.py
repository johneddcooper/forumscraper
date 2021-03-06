import BeautifulSoup
from BeautifulSoup import BeautifulSoup as bs
from math import sqrt
import sys
import re
import argparse
import pdb
import itertools
import string
import operator
import pprint
import pickle
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

##################################
#     public Scraper class       #
##################################

class Scraper:
    #############################
    #       Public methods      #
    #############################
    
    def __init__(self, soups=None, save=None):
        if save:
            self.load(save)
        elif soups:
            self.train(soups)
    
    def load(self, save):
        self.labels, self.clusters, self.use_text, \
            self.depth, self.outliar_names = pickle.load(open(save))

    def train(self, soups):
        """Train over list of soups to find location/names of relevant tags"""
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
             open("gfb.p", "w"))

    def scrape(self, soup):
        contents = self.parse(soup)
        cd = self.label_contents(contents)
        return cd
    
    ##################################
    #       Internal functions       #
    ##################################
   
    def get_labels(self, contents):
        """Query user to label data.
        """
        labels = {}
        clusters = {}
        use_text = {}
        for i,c in enumerate(contents):
            pprint.pprint(c)
            label = raw_input("Label ((D) discard): ").lower().strip()
            if label != 'd':
                print "Store text instead of raw tags?"
                for elem in c:
                    print elem.text
                text = raw_input("Store text instead of raw tags? (y/[n]) ").lower().strip()
                if text == 'y':
                    use_text[label] = True
                else:
                    use_text[label] = False
            else:
                label = "d%d"%i
            na = self.name_attr(c[0])
            if na in labels.keys():
                labels[na].append(label)
            else:
                labels[na] = [label]
            stats = self.calc_stats(c)
            clusters[stats] = label
            print "----------"
        return labels, clusters, use_text
    
    def parse(self, soup):
        """Extracts content of a soup, given training data"""
        if not self.depth:
            print "Error: Need to train data first."
            return
        tbd = self.get_tags_by_depth(soup)
        tags = [self.get_tags_by_string(out, tbd[self.depth]) for out in self.outliar_names]
        contents = self.extract_contents(tags)
        return contents 
    
    def label_contents(self, contents):
        content_dict = {}
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
                    print cands
                    stat = self.calc_stats(c)
                    calc_diff = lambda x, y: mean([abs(x[i]-y[i]) for i in xrange(len(x))])
                    
                    min_diff = 100000
                    min_label = ""
                    for k in cands.keys():
                        d = calc_diff(stat, k)
                        if d < min_diff:
                            min_diff = d
                            min_label = cands[k]
                    content_dict[cands[k]] = c

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
        avglen = mean(map(len, map(str,tags)))
        numdig = mean(map(lambda x: count(x, string.digits), map(lambda x: x.getText(), tags)))
        numupper = mean(map(lambda x: count(x, string.ascii_uppercase), map(lambda x: x.getText(), tags)))
        numwhite = mean(map(lambda x: count(x, string.whitespace), map(lambda x: x.getText(), tags)))
        return numdig/avglen, numupper/avglen, numwhite/avglen

##################################
# Miscellanious numeric functions#
##################################

def mean(li):
    """returns mean of a list"""

    return float(sum(li))/len(li)

def std(li):
    """returns standard deviation of a list"""

    m = mean(li)
    return sqrt(mean([abs(x-m) for x in li]))



def of(name, num, suffix=""):
    """open file: for internal testing purposes"""
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

