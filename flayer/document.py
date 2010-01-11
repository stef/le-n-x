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

debug = True

import sys
sys.path.append('..')
from fetch.cache import Cache
import fetch.hunspell
from BeautifulSoup import BeautifulSoup
import nltk.tokenize
from operator import itemgetter

EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

LANG='en_US'
DICTDIR='/usr/share/hunspell/'
DICT=DICTDIR+LANG

cache=Cache('../cache');

class Doc:
    def __init__(self,id):
        self.__dict__={}
        self.__dict__['id'] = id
        #self.__dict__['lang'] = id.split(":")[-2]
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
        elif name == "tokenfreq":
            self.__dict__[name]=self.gettokenfreq()
        elif name == "stemfreq":
            self.__dict__[name]=self.getstemfreq()
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else:  raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else:  raise AttributeError, name

    def gettext(self):
        soup = BeautifulSoup(self.raw)
        try:
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

    def gettokenfreq(self):
        return map(
            lambda x: (x[0],len(x[1])),
            sorted(self.wpos.items(),
                   lambda x,y: cmp(len(x),len(y)),
                   itemgetter(1),
                   reverse=True))

    def getstems(self):
        # start stemming
        engine = fetch.hunspell.HunSpell(DICT+'.dic', DICT+'.aff')
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

    def getstemfreq(self):
        return map(
            lambda x: (x[0],len(x[1])),
            sorted(filter(lambda x: x[0],
                          self.spos.items()),
                   lambda x,y: cmp(len(x),len(y)),
                   itemgetter(1),
                   reverse=True))

if __name__ == "__main__":
    import difflib

##     f=open("cankor",'r')
##     docs=f.readlines()
##     d1=Doc("Canada")
##     d2=Doc("Korea")
##     matcher = difflib.SequenceMatcher(None,d1.stems,d2.stems)
##     for match in matcher.get_matching_blocks():
##         if match[2]:
##             d1.quotes[d2.id]=match
##             d2.quotes[d1.id]=match
##     db=[d1,d2]
##     for d in docs:
##         newd=Doc(d)
##         for oldd in db:
##             matcher = difflib.SequenceMatcher(None,newd.stems,oldd.stems)
##             for match in matcher.get_matching_blocks():
##                 if match[2]:
##                     newd.quotes[oldd.id]=(match[0],match[2])
##                     oldd.quotes[newd.id]=(match[1],match[2])
##         if newd.quotes:
##             db.append(newd)
##     frags={}
##     for d in db:
##         for (k,v) in d.quotes.items():
##             frag=' '.join(d.tokens[v[0]:v[0]+v[1]]).encode('utf8')
##             frags[frag]=frags.get(frag,[])+[k]
##     for (k,v) in sorted(frags.items(),key=lambda x: len(x[1])):
##         print k, '.-.>', v

    d1=Doc(sys.argv[1])
    d2=Doc(sys.argv[2])
    matcher = difflib.SequenceMatcher(None,d1.stems,d2.stems)
    res = matcher.get_matching_blocks()
    for match in sorted(res,key=itemgetter(2),reverse=True):
        if match[2]:
            print "token offsets:", match[0], '@canada - ', match[1], '@'+sys.argv[1]
            print ' '.join(d1.tokens[match[0]:match[0]+match[2]]).encode('utf8')
            print ' '.join(d2.tokens[match[1]:match[1]+match[2]]).encode('utf8')
            print "----------------------------------------------"


