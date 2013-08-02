import BeautifulSoup
from BeautifulSoup import BeautifulSoup as bs
from math import sqrt
import sys
import re
import argparse
import pdb

# Delete this eventually
def similarity(L1, L2):
    """ similarity(L1, L2)
    Takes two lists of BeautifulSoup tags
    Returns the number of UNIQUE name-attr pairs that are not shared by both, normalized by total number of unique pairs

    """
    d1 = tag_distribution(L1)
    d2 = tag_distribution(L2)
    mismatches = 0
    for k1 in d1.keys():
        if k1 not in d2.keys():
            mismatches += 1 

    for k2 in d2.keys():
        if k2 not in d1.keys():
            mismatches += 1

    return float(mismatches)/(len(d1.keys())+len(d2.keys()))

def mean(li):
    """returns mean of a list"""

    return float(sum(li))/len(li)

def std(li):
    """returns standard deviation of a list"""
    m = mean(li)
    return sqrt(mean([abs(x-m) for x in li]))

def strip_links(L):
    """Returns list of BeautifulSoup tags without the links."""
    return filter(lambda x: x.name!='a', L)

def get_tags_by_depth(soup):
    """get_tags_by_depth(soup)
    Takes a BeautifulSoup object. Returns a list [d0, d1, ..., dn],
    where d_i is a list of the BeautifulSoup.Tag objects at that given depth level.
    For example:
    d0=[<head>..</head>, <body>..</body>]
    d1=[<meta>.., <table>.., <script>..]

    """
    tags_by_depth = [[t for t in soup(recursive=False)]]
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
def tag_distribution(L):
    """tag_distribution(L):
    L is a list of BeautifulSoup.Tag objects
    -Uses tag name and attributes to generate a dictionary of counts.
    -Strips all links.
    -Replaces all series of numbers with a single x.

    E.g. [BeautifulSoup("<div class=post32124></div>")] returns {'div-postx': 1}

    """
    ud = {}
    for x in L:
        n = name_attr(x)
        if n:
            if n in ud.keys():
                ud[n] += 1
            else:
                ud[n] = 1
    return ud

def same_tags(L1, L2):
    """same_tags(L1, L2)
    L1 and L2 are lists of BeautifulSoup.Tag objects
    Returns True iff all tags in one list are in the other.
    
    """ 
    
    s1 = set(tag_distribution(L1).keys())
    s2 = set(tag_distribution(L2).keys())


    return all(k1 in s2 for k1 in s1) and \
            all(k2 in s1 for k2 in s2)


def name_attr(tag, strip_nums=1, strip_orphans=1, strip_links=1):
    """name_attr(tag, strip_nums=1, strip_orphans=1, strip_links=1)
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

def pn(L):
    """Print name: Calls name_attr() on all elements in list of BeautifulSoup.Tag objects."""
    return filter(None, map(name_attr, L))

def of(name, num, suffix=""):
    soups = []
    for i in xrange(1, int(num)+1):
        soups.append(bs(open("%s%s%s"%(name,str(i),suffix)).read()))
    return soups

def get_tags_by_string(na, L):
    """get_tags_by_string(string, list of BeautifulSoup.Tag objects)
    Takes a name-attr string (as returned by name_attr()) and returns tags that match

    """
    
    return filter(lambda x: name_attr(x)==na, L)

def get_outliars_from_dict(dic):
    """get_outliars_from_dict(dictionary)
    Takes a dictionary where the values are integer counts.
    Returns a list of the keys where the values are two standard deviations above the mean.

    """
    m = mean(dic.values())
    s = std(dic.values())
    k = filter(lambda x: x[1] > m + 2*s, dic.items())
    if k:
        return zip(*k)[0]

def outliars(page_tbd, d):
    """outliars(page_tags_by_depth, depth)
   
    Returns all tags that appear disproportionately often at the given depth.
    """

    outliars = get_outliars_from_dict(tag_distribution(page_tbd[d]))
    if not outliars:
        return []
    out_tags = (get_tags_by_string(x, page_tbd[d]) for x in outliars)
   
    out_tags_no_boring = []
    for i, x in enumerate(out_tags):
        if any(not e.text for e in x):
            continue
        if all(e.text==x[0].text for e in x):
            continue
        out_tags_no_boring.append(x)

    return out_tags_no_boring

def pprint_file(obd):
    """pprint_file(outliars_by_depth)
    pretty prints element of list returned by call to get_outliars_by_depth().

    """
    matches = map(None, *obd)
    for i,m in enumerate(matches):
        print "------%d------" % i
        for x in m:
            print x
            print "..."

def strip_textless_tags(t):
    i = 0
    c = 0
    for f in t:
        for ol in f:
            for tag in ol:
                for comment in tag.findChildren()(
                        text=lambda text:
                        isinstance(text, BeautifulSoup.Comment)
                                          ):
                    comment.extract()
                    c+=1
                for child in tag.findChildren():
                    if len(child.text) == 0 and \
                        not child.first('img') and \
                        child.name != 'img':
                        child.extract()
                        i+=1
    print "extracted %d empty tags and %d comments" % (i, c)
    

def extract_content(t):
    new_t = []
    for page in t:
        new_page = []
        for outliar in page:
            new_outliars = []
            visited = []
            all_children_n = [map(name_attr, inst.findChildren()) for inst in outliar]
            all_children = [inst.findChildren() for inst in outliar]
            ac_pairs = zip(all_children_n, all_children)
            for acn, ac in ac_pairs:
                if all(acn in other for other in all_children_n):
                    visited.append(acn)
                    print c, map(name_attr, tag)
                    
                    new_outliars.append(tag)
            new_page.append(new_outliars)
        new_t.append(new_page)
    return new_t

#### Todo:
#### Finish structure_stats, use it to compute simlarity metrics,
#### refer to data structure drawing if you get confused

def structure_stats(T):
    """Takes BeautifulSoup tag structure
    Returns
        1) their maximum depth
        2) the total number of nested tags
    
    """
    similarity = 0

    # Both are not the same type, eg NavigableString and Tag, so return 0
    if type(T1) != type(T2):
        return 0

    # Neither are tags, but are same type, so return 1 for max similarity
    if type(T1) != BeautifulSoup.Tag:
        return 1
    
    remaining_tags = filter(lambda x: type(x) == BeautifulSoup.Tag, T1)
    depth+=1
    

if len(sys.argv) < 4:
    print "usage: python tester.py dir # suffix"

soups = of(sys.argv[1], sys.argv[2], sys.argv[3])
P = len(soups)

dbfs = map(get_tags_by_depth, soups)
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
print "Beginning comparison at depth level", len(fbds)/3

for i in range(len(fbds)/3, len(fbds)-1):
    if not all(same_tags(x1, x2) for x1 in fbds[i] for x2 in fbds[i]):
        print "Not all tags at depth level %d are the same"%i
        break
    """
    sim_matrix = [similarity(x1, x2) for x1 in fbds[i] for x2 in fbds[i]]
    print i, std(map(len, fbds[i]))
    if sum(sim_matrix) != 0:
        print "No longer closely related."
        break
    """
t = [outliars(dbfs[x], i) for x in xrange(P)]

strip_textless_tags(t)

newt = []

# this takes each post, which consists of several large and nested
# div/tables, and extracts the subcontents that are identical
# across posts

for item in t[0]:
    
    children = [tag() for tag in item]
    children = filter(None, children)

    allnames = [filter(None, map(name_attr, ch)) for ch in children]
    allnames = filter(None, allnames) 

    # if an attribute is in all of the children, then extract it
    # and display it as an independent element
    
    if allnames:

        # which tags do all the posts have in common?
        # we want common tags because they are likely to indicate
        # structural similarities, like postdates/usernames
        # rather than tags from within posts
        
        common = reduce(lambda x, y: x.intersection(y), map(set, allnames))
        # extract the actual tags based off their names/attributes
    
        newti = [[get_tags_by_string(com, c) for com in common] for c in children]
       
        # extract these tags from their parents
        [[[x.extract() for x in a] for a in b] for b in newti]

        # some of these tags are redundant. if they are exactly
        # the same across the posts, then strip them.
        
        newtz = zip(*newti)
        for i in range(len(newtz)):
            if all(x==newtz[i][0] for x in newtz[i]):
                map(lambda n: n.pop(i), newti)
        if newti:
            newt.append(newti)

znewt = zip(*newt)
strip_textless_tags(t)
