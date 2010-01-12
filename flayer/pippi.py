#!/usr/bin/env python
#    This file is part of le-n-x.

#    utterson is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    utterson is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with utterson.  If not, see <http://www.gnu.org/licenses/>.

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

# usage: python pippi.py Doc1 Doc2
# where Doc1 and Doc2 either are valid Celex or OJ ids on eur-lex, in which
# case the tool automatically fetches these docs and caches them before
# analysis. 
#
# Doc1 and Doc2 can also be any kind of html file in the cache. If you have
# docs that are not available on eur-lex: 
#     1. download them, 
#     2. important: convert - if necessary - to html
#     3. important: enclose the text to analyse into <div id="TexteOnly"> tags 
#     4. store these files in the cache
#     5. run pippi. it should find the files in the cache and analyze them properly.
#
# setup. you need pyhunspell, the english hunspell dictionary, nltk, and
# beautiful soup. check the import section later.
# you also need to set an existing cache directory.

EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="
LANG='en_US'
DICTDIR='/usr/share/hunspell/'
DICT=DICTDIR+LANG
CACHEDIR='../cache'

import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?

import re
import sys
import urllib2
from operator import itemgetter

filterre=re.compile("http://eur-lex\.europa\.eu/LexUriServ/LexUriServ\.do\?uri=(.*)")
cache=None

class Cache:
    def __init__(self,dir):
        self.__dict__={}
        self.__dict__['basedir'] = dir

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else:  raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else:  raise AttributeError, name

    """ returns the contents of an url either from the cache or the web """
    def fetchUrl(self,url):
        filter=re.match(filterre,url)
        if(not filter): return
        id=filter.group(1)
        try:
            f = open(self.basedir+'/'+id, 'r')
        except IOError:
            text = urllib2.urlopen(url).read()
            # write out cached object
            f = open(self.basedir+'/'+id, 'w')
            f.write(text)
            f.close()
        else:
            text = f.read()
        f.close()
        return text

class Doc:
    def __init__(self,id):
        self.__dict__={}
        self.__dict__['id'] = id
        # TODO this needs some more cleaning up in regards of stupid encodings
        self.__dict__['raw'] = cache.fetchUrl(EURLEXURL+id) #.decode('utf-8')
        self.__dict__['quotes'] = {}

    def __getattr__(self, name):
        if name == "text":
            self.__dict__['text']=self.gettext()
        elif name in ["tokens", "wpos"]:
            (self.__dict__['tokens'],self.__dict__['wpos'])=self.gettokens()
        elif name in ["stems", "spos"]:
            self.__dict__['stems']=self.getstems()
            (self.__dict__['stems'],self.__dict__['spos'])=self.getstems()
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else:  raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else:  raise AttributeError, name

    def __repr__(self):
        return "%s" % self.id

    def gettext(self):
        soup = BeautifulSoup(self.raw)
        try:
            # TexteOnly is the id used in eur-lex,
            # if you provide your own files, please
            # put the relevant part between
            # <div id="TexteOnly"> tags.
            txt=soup.find(id='TexteOnly').findAll(text=True)
            return txt
        except:
            return None

    def gettokens(self):
        # start tokenizing
        tokens=[]
        wpos={}
        i=0
        for frag in self.text:
            if not frag: continue
            words=nltk.tokenize.wordpunct_tokenize(unicode(frag))
            tokens+=words
            # store positions of words
            for word in words:
                wpos[word]=wpos.get(word,[])+[i]
                i+=1
        return (tokens,wpos)

    def getstems(self):
        # start stemming
        engine = hunspell.HunSpell(DICT+'.dic', DICT+'.aff')
        stems=[]
        spos={}
        i=0
        for word in self.tokens:
            # stem each word and count the results
            stem=tuple(engine.stem(word.encode('utf8')))
            stems.append(stem)
            spos[stem]=spos.get(stem,[])+[i]
            i+=1
        return (stems,spos)

class MatchDb:
    def __init__(self):
        self.__dict__={}
        self.__dict__['docs'] = []
        self.__dict__['db'] = {}

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else:  raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else:  raise AttributeError, name

    def addMatch(self,doc1,doc2,match):
        m1=(doc1,match[0],match[2])
        m2=(doc2,match[1],match[2])
        stem=tuple(doc1.stems[match[0]:match[0]+match[2]])
        if not self.db.has_key(stem): self.db[stem]=[]
        if not m1 in self.db[stem]: self.db[stem].append(m1)
        if not m2 in self.db[stem]: self.db[stem].append(m2)
        doc1.quotes[doc2.id]=(match[0],match[2])
        doc2.quotes[doc1.id]=(match[1],match[2])

    def analyze(self,doc1,doc2):
        if doc1==doc2: return
        print "analyzing",doc1.id,"and",doc2.id
        matcher = difflib.SequenceMatcher(None,doc1.stems,doc2.stems)
        for match in matcher.get_matching_blocks():
            if match[2]: self.addMatch(doc1,doc2,match)
        if not doc1 in self.docs: self.docs.append(doc1)
        if not doc2 in self.docs: self.docs.append(doc2)

    def dump(self):
        return "%s\n%s" % (self.docs,self.db)

    def stats(self):
        print "number of multigrams:", len(filter(lambda x: len(x)>2,self.db.keys()))
        longestfrags=sorted(self.db.items(),reverse=True,cmp=lambda x,y: cmp(len(x[0]), len(y[0])))
        print "max len of frag:", len(longestfrags[0][0])
        print "longest frags"
        for (k,docs) in longestfrags:
            for d in docs:
                print d,":"," ".join(d[0].tokens[d[1]:d[1]+d[2]]).encode('utf8')
                print
            print '-----'

if __name__ == "__main__":
    import difflib

    cache=Cache(CACHEDIR)
    db=MatchDb()
    d1=Doc(sys.argv[1])
    d2=Doc(sys.argv[2])
    db.analyze(d1,d2)
    db.stats()
