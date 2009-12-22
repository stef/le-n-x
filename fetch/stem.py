#!/usr/bin/env python

import hunspell
import nltk.tokenize
from BeautifulSoup import BeautifulSoup
from operator import itemgetter

stopwords=['the','of','and','in','to','for','by','that',
           'a','on','at','as','from','it','this', 'with',
           'into','their','also']
# remove single digits
stopwords+=[str(x) for x in range(0,10)]
# remove single chars
stopwords+=[chr(x) for x in range(ord('a'),ord('z'))+range(ord('A'),ord('Z'))]

""" renders a tagcloud using <span> tags """
def renderspan(tags,len=None):
    return ' '.join([('<span class="size%d">%s</span>'%
                      (min(1+p*9/max(map(itemgetter(1), tags)), 9), x)) for (x, p) in sorted(tags[0:len])])

"""
renders a tagcloud using <font size="%d"> tags:
param limit of tags to be rendered """
def renderfont(tags,len=None):
    return ' '.join([('<font size="%d">%s</font>'%
                      (min(1+p*9/max(map(itemgetter(1), tags)), 9), x)) for (x, p) in sorted(tags[0:len])])

"""
returns a hunspell object
param: language code """
def init(lang='en_US'):
    return hunspell.HunSpell('/usr/share/hunspell/'+lang+'.dic', '/usr/share/hunspell/'+lang+'.aff')

""" returns the text-only version of the main content (identified by id="TexteOnly") """
def scrapeContent(file):
    soup = BeautifulSoup(file)
    return soup.find(id='TexteOnly').findAll(text=True)

""" converts a text into a list of weighted words """
def gentags(text):
    tags={}
    # start tokenizing
    engine = init()
    for frag in text:
        tokens = nltk.tokenize.wordpunct_tokenize(frag)
        for word in tokens:
            # stem each word and count the results
            stems=engine.stem(word.encode('utf8'))
            # simple: use the first returned stem
            if stems: tags[stems[0]]=1+tags.get(stems[0],0)
            # not-so-simple: use all stems
            #for stem in stems:
            #    tags[stem]=1+tags.get(stem,0)
    # remove stopwords
    for stopword in stopwords:
        if tags.has_key(stopword): del tags[stopword]

    # transform dict into desc sorted list of (tag,value) tuples.
    return sorted([x for x in tags.items()],reverse=True,key=itemgetter(1))

def tagcloud(file,limit=None):
    return renderfont(gentags(scrapeContent(file)),limit)

if __name__ == "__main__":
    f=open('/home/stef/data/eu/01 General, financial and institutional matters/0140 Provisions governing the institutions/32003D0174/EN', 'r')
    print gentags(scrapeContent(f))
    print tagcloud(f)
