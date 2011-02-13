#!/usr/bin/env python
#    This file is part of le-n-x.

#    le(n)x is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    le(n)x is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with le(n)x  If not, see <http://www.gnu.org/licenses/>.

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

import hunspell
import nltk.tokenize
from BeautifulSoup import BeautifulSoup
from operator import itemgetter
import math
from django.core.management import setup_environ
from lenx import settings
setup_environ(settings)
from stopwords import stopwords

"""calculates log weight over a list"""
def log2lin(a, pmax, classes): return int(round((classes-1)*((math.exp(a))/pmax)))

def stemFreq(stems):
    tags={}
    # start tokenizing
    for stem in stems:
       if not stem:
          continue
       stop=False
       for s in stem:
          if s in stopwords:
             stop=True
             break
       if not stop:
          tags[stem[0]]=1+tags.get(stem[0],0)
    return tags

def wordFreq(text):
    tags={}
    # start tokenizing
    engine = engine = hunspell.HunSpell(settings.DICT+'.dic', settings.DICT+'.aff')
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
    return tags

""" converts a text into a list of weighted words """
def gentags(text):
    tags=wordFreq(text)
    # transform dict into desc sorted list of (tag,value) tuples.
    return sorted([x for x in tags.items()],reverse=True,key=itemgetter(1))

def logTags(stems,l=None,tags=None,classes=9):
    if not tags and stems: tags=stemFreq(stems)
    if not tags:
        return []
    pmax=max(tags.values())

    tags=sorted(
          [(word, log2lin(math.log(weight),pmax,classes)) for (word,weight) in tags.items() if weight],
          reverse=True,
          key=itemgetter(1))[0:l]

    return [{'weight': min(1+p*9/max(map(itemgetter(1), tags)), 9),
             'tag':  x}
             for (x, p) in tags]

""" renders a tagcloud using <span> tags """
def renderspan(tags,l=None,classes=9):
    tags=sorted(tags[0:l])
    pmax=max(tags,key=itemgetter(1))[1]
    # recalculate logarithmic weights
    tags=map(lambda x: (x[0],log2lin(x[1],pmax,classes)),  map(lambda x: (x[0],math.log(x[1])), tags))
    return ' '.join([('<span class="size%d">%s</span>'%
                      (min(1+p*9/max(map(itemgetter(1), tags)), 9), x)) for (x, p) in tags])

""" returns the text-only version of the main content (identified by id="TexteOnly") """
def scrapeContent(file):
    soup = BeautifulSoup(file)
    try:
        txt=soup.find(id='TexteOnly').findAll(text=True)
    except:
        return None
    return txt

def tagcloud(file,limit=None):
    return renderspan(gentags(scrapeContent(file)),limit)
