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
from django.conf import settings
DICTDIR=settings.DICT_PATH
LANG='en_US'
DICT=DICTDIR+'/'+LANG

# german stopwords: http://feya.solariz.de/wp-content/uploads/stopwords.txt
# other languages (also hungarian) can be found here: http://snowball.tartarus.org/algorithms/
# src: http://armandbrahaj.blog.al/2009/04/14/list-of-english-stop-words/
stopwords=['a', 'about', 'above', 'above', 'across', 'after', 'afterwards', 'again',
           'against', 'all', 'almost', 'alone', 'along', 'already',
           'also','although','always','am','among', 'amongst', 'amoungst', 'amount',
           'an', 'and', 'another', 'any','anyhow','anyone','anything','anyway',
           'anywhere', 'are', 'around', 'as',  'at', 'back','be','became',
           'because','become','becomes', 'becoming', 'been', 'before', 'beforehand',
           'behind', 'being', 'below', 'beside', 'besides', 'between', 'beyond', 'bill',
           'both', 'bottom','but', 'by', 'call', 'can', 'cannot', 'cant', 'co', 'con',
           'could', 'couldnt', 'cry', 'de', 'describe', 'detail', 'do', 'done', 'down',
           'due', 'during', 'each', 'eg', 'eight', 'either', 'eleven','else', 'elsewhere',
           'empty', 'enough', 'etc', 'even', 'ever', 'every', 'everyone', 'everything',
           'everywhere', 'except', 'few', 'fifteen', 'fify', 'fill', 'find', 'fire',
           'first', 'five', 'for', 'former', 'formerly', 'forty', 'found', 'four', 'from',
           'front', 'full', 'further', 'get', 'give', 'go', 'had', 'has', 'hasnt', 'have',
           'he', 'hence', 'her', 'here', 'hereafter', 'hereby', 'herein', 'hereupon',
           'hers', 'herself', 'him', 'himself', 'his', 'how', 'however', 'hundred', 'ie',
           'if', 'in', 'inc', 'indeed', 'interest', 'into', 'is', 'it', 'its', 'itself',
           'keep', 'last', 'latter', 'latterly', 'least', 'less', 'ltd', 'made', 'many',
           'may', 'me', 'meanwhile', 'might', 'mill', 'mine', 'more', 'moreover', 'most',
           'mostly', 'move', 'much', 'must', 'my', 'myself', 'name', 'namely', 'neither',
           'never', 'nevertheless', 'next', 'nine', 'no', 'nobody', 'none', 'noone',
           'nor', 'not', 'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once',
           'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our', 'ours',
           'ourselves', 'out', 'over', 'own','part', 'per', 'perhaps', 'please', 'put',
           'rather', 're', 'same', 'see', 'seem', 'seemed', 'seeming', 'seems', 'serious',
           'several', 'she', 'should', 'show', 'side', 'since', 'sincere', 'six', 'sixty',
           'so', 'some', 'somehow', 'someone', 'something', 'sometime', 'sometimes',
           'somewhere', 'still', 'such', 'system', 'take', 'ten', 'than', 'that', 'the',
           'their', 'them', 'themselves', 'then', 'thence', 'there', 'thereafter',
           'thereby', 'therefore', 'therein', 'thereupon', 'these', 'they', 'thickv',
           'thin', 'third', 'this', 'those', 'though', 'three', 'through', 'throughout',
           'thru', 'thus', 'to', 'together', 'too', 'top', 'toward', 'towards', 'twelve',
           'twenty', 'two', 'un', 'under', 'until', 'up', 'upon', 'us', 'very', 'via',
           'was', 'we', 'well', 'were', 'what', 'whatever', 'when', 'whence', 'whenever',
           'where', 'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon',
           'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever', 'whole',
           'whom', 'whose', 'why', 'will', 'with', 'within', 'without', 'would', 'yet',
           'you', 'your', 'yours', 'yourself', 'yourselves',
           'shall', "Europa", "European", "states", "quot", "gt", "directive",
           "member", "article" ]
# remove single digits
stopwords+=[str(x) for x in range(0,10)]
# remove single chars
stopwords+=[chr(x) for x in range(ord('a'),ord('z'))+range(ord('A'),ord('Z'))]

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
    engine = engine = hunspell.HunSpell(DICT+'.dic', DICT+'.aff')
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

def logTags(stems,l=None,classes=9):
    tags=stemFreq(stems)
    pmax=max(tags.values())

    tags=sorted(
          [(word, log2lin(math.log(weight),pmax,classes)) for (word,weight) in tags.items()],
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
