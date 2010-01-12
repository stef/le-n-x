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

    def __repr__(self):
        return "%s" % self.id

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
        print "number of total common phrases:", len(self.db)
        print "number of multigrams:", len(filter(lambda x: len(x)>2,self.db.keys()))
        print "most frequent frags"
        topfrags=sorted(self.db.items(),reverse=True,cmp=lambda x,y: cmp(len(x[1]), len(y[1])))
        for (k,docs) in topfrags[:100]:
            print "%d: %s" % (len(docs)," ".join(docs[0][0].tokens[docs[0][1]:docs[0][1]+docs[0][2]]).encode('utf8'))

        longestfrags=sorted(self.db.items(),reverse=True,cmp=lambda x,y: cmp(len(x[0]), len(y[0])))
        print "max len of frag:", len(longestfrags[0][0])
        print "longest frags"
        for (k,docs) in longestfrags:
            for d in docs:
                print "\t",d,":"," ".join(d[0].tokens[d[1]:d[1]+d[2]]).encode('utf8')
            print '-----'

if __name__ == "__main__":
    import difflib

    db=MatchDb()
    d1=Doc("Canada")
    d2=Doc("Korea")
    db.analyze(d1,d2)
    f=open("cankor",'r')
    docs=f.readlines()
    for d in docs:
        newd=Doc(d.strip('\t\n'))
        for oldd in db.docs:
            db.analyze(newd,oldd)
    #print db.stats()

#import sqlobject
#import sys, os, platform
#if(platform.machine()=='i686'):
   #import psyco
#sqlobject.sqlhub.processConnection = sqlobject.connectionForURI('sqlite:' + DBPATH)
#class Message(sqlobject.SQLObject):
    #""" represents a message object """
    #delivered = sqlobject.col.DateTimeCol()
    #messageid = sqlobject.col.StringCol()
    #headers = sqlobject.SQLMultipleJoin("HeaderValue")
    #sender = sqlobject.col.ForeignKey("Email")
    #path = sqlobject.col.StringCol()

   #def main():
      #""" this function creates a new database"""
      #Header.createTable(ifNotExists = True)
      #HeaderValue.createTable(ifNotExists = True)
      #Person.createTable(ifNotExists = True)
      #Email.createTable(ifNotExists = True)
      #Role.createTable(ifNotExists = True)
      #Message.createTable(ifNotExists = True)
   #psyco.full()
   #sys.exit(main())
