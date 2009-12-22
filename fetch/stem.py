#!/usr/bin/env python

import hunspell
import nltk.tokenize
from BeautifulSoup import BeautifulSoup
from operator import itemgetter

stopwords=['the','of','and','in','to','for','by','that',
           'a','on','at','as','from','it','this', 'with',
           'into','their','also']

def renderspan(tags,len=None):
    return ' '.join([('<span class="size%d">%s</span>'%(min(1+p*5/max(map(lambda x: x[1], tags)), 5), x)) for (x, p) in sorted(tags[0:len])])

def renderfont(tags,len=None):
    return ' '.join([('<font size="%d">%s</font>'%(min(1+p*5/max(map(lambda x: x[1], tags)), 5), x)) for (x, p) in sorted(tags[0:len])])

def init(lang='en_US'):
    return hunspell.HunSpell('/usr/share/hunspell/'+lang+'.dic', '/usr/share/hunspell/'+lang+'.aff')

def scrapeContent(file):
    soup = BeautifulSoup(file)
    return soup.find(id='TexteOnly').findAll(text=True)

def gentags(text):
    tags={}
    # start tokenizing
    engine = init()
    for frag in text:
        tokens = nltk.tokenize.wordpunct_tokenize(frag)
        for word in tokens:
            # stem each word and count the results
            for stem in engine.stem(word.encode('utf8')):
                tags[stem]=1+tags.get(stem,0)
    # remove stopwords and single digits
    for stopword in stopwords+[str(x) for x in range(0,10)]:
        if tags.has_key(stopword): del tags[stopword]

    # transform dict into sorted list of (tag,value) tuples.
    return sorted([x for x in tags.items()],reverse=True,key=itemgetter(1))

def tagcloud(file,limit=None):
    return renderfont(gentags(scrapeContent(file)),limit)

if __name__ == "__main__":
    f=open('/home/stef/data/eu/01 General, financial and institutional matters/0140 Provisions governing the institutions/32003D0174/EN', 'r')
    print gentags(scrapeContent(f))
    #print tagcloud(f)
