#!/usr/bin/env python
#    This file is part of le(n)x.

#    le(n)x is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    le(n)x is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with le(n)x.  If not, see <http://www.gnu.org/licenses/>.

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

DICTDIR='/usr/share/hunspell/'
import cache as Cache
CACHE=Cache.Cache('cache');
from fsdb import FilesystemDB
FSDB=FilesystemDB('db')

import difflib
import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?

LANG='en_US'
DICT=DICTDIR+LANG
EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

""" class representing a distinct document, does stemming, some minimal nlp, can be saved and loaded """
class Doc:
    def __init__(self,id,cache=CACHE,storage=FSDB):
        self.__dict__={}
        self.__dict__['id'] = id
        #self.__dict__['lang'] = id.split(":")[-2]
        self.__dict__['raw'] = cache.fetchUrl(EURLEXURL+id).decode('utf-8')
        self.__dict__['refs'] = {}
        self.__dict__['attrs'] = ['text','tokens','stems','refs','wpos','spos']
        if storage.getDict("docs"+self.id,create=False):
            self.load()

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        elif name == "text":
            self.__dict__['text']=self.gettext()
        elif name in ["tokens", "wpos"]:
            (self.__dict__['tokens'],self.__dict__['wpos'])=self.gettokens()
        elif name in ["stems", "spos"]:
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
        # TexteOnly is the id used on eur-lex pages containing distinct docs
        return [unicode(x) for x in soup.find(id='TexteOnly').findAll(text=True)]

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

    def addRef(self,stem,match,ref):
        if not self.refs.has_key(stem): self.refs[stem]={'matches':[],'refs':[]}
        if not match in self.refs[stem]['matches']:
            self.refs[stem]['matches'].append(match)
        if not ref.id in self.refs[stem]['refs']:
            self.refs[stem]['refs'].append(ref.id)

    def getFrag(self,start,len):
        return " ".join(self.tokens[start:start+len]).encode('utf8')

    def save(self,dir="docs",storage=FSDB):
        dbdir=storage.getDict(dir+"/"+self.id)
        for attr in self.attrs:
            storage.storeVal(dbdir+"/"+attr,self.__getattr__(attr))

    def load(self,dir="docs",storage=FSDB):
        dbdir=storage.getDict(dir+"/"+self.id,create=False)
        if dbdir:
            for attr in self.attrs:
                self.__dict__[attr]=storage.loadVal(dbdir+"/"+attr)

class MatchDb:
    def __init__(self):
        self.__dict__={}
        self.__dict__['docs'] = {}
        self.__dict__['db'] = {}

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else:  raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else:  raise AttributeError, name

    def getMatches(self,doc1,doc2):
        return difflib.SequenceMatcher(None,doc1.stems,doc2.stems).get_matching_blocks()

    def storeMatch(self,doc1,doc2,match):
        if not match[2] or doc1.id==doc2.id: return (doc1,doc2)
        m1=(match[0],match[2])
        m2=(match[1],match[2])
        stem=tuple(doc1.stems[match[0]:match[0]+match[2]])
        if not self.db.has_key(stem): self.db[stem]=[]
        if not (doc1.id,)+m1 in self.db[stem]: self.db[stem].append((doc1.id,)+m1)
        if not (doc2.id,)+m2 in self.db[stem]: self.db[stem].append((doc2.id,)+m2)
        doc1.addRef(stem,m1,doc2)
        doc2.addRef(stem,m2,doc1)
        return (doc1,doc2)

    def analyze(self,doc1,doc2):
        if doc1.id in self.docs.keys() and doc2.id in self.docs.keys(): return
        #print u"analyzing",doc1.id,u"and",doc2.id
        for match in self.getMatches(doc1,doc2):
            doc1,doc2=self.storeMatch(doc1,doc2,match)
        return (doc1,doc2)

    def save(self,storage=FSDB):
        for doc in self.docs.values():
            doc.save(storage=storage)
        storage.storeVal("matches",self.db)

    def load(self,storage=FSDB,cache=CACHE):
        try:
            self.db=storage.loadVal("matches") or {}
        except:
            return
        for doc in storage.getKeys("docs"):
            d=Doc(doc,cache=cache,storage=storage)
            d.load(storage=storage)
            self.docs[doc]=d
        return True

    def longestFrags(self):
        return sorted(self.db.items(),
                      reverse=True,
                      cmp=lambda x,y: cmp(len(x[0]), len(y[0])))

    def insert(self,doc):
        if doc.id in self.docs.keys(): return
        for old in self.docs.values():
            # order reversed for identical output with bulkadd
            old,doc=self.analyze(old,doc)
            self.docs[old.id]=old
        self.docs[doc.id]=doc

if __name__ == "__main__":
    db=MatchDb()
    print "loading..."
    db.load(cache=Cache.Cache('../cache'),
            storage=FilesystemDB('../db'))
    print "done"
