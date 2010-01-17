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
cache=Cache.Cache('cache');

import sys, os, platform
import hashlib, cPickle, difflib
from operator import itemgetter
import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?

if(platform.machine()=='i686'):
    import psyco
    psyco.full()

LANG='en_US'
DICT=DICTDIR+LANG
EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

""" some helper fns for a very simple file- and cPickle-based key-value store of computed data"""
def getDict(dir,create=True):
    if not os.path.exists(dir):
        if create:
            os.mkdir(dir)
        else:
            return None
    return dir

def storeVal(key,value):
    file=open(key,'w')
    file.write(value)
    file.close()

def loadVal(key):
    file=open(key,'r')
    res=file.read()
    file.close()
    return res

""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag.decode('utf8'))

""" class representing a dictinct document, does stemming, some minimal nlp, can be saved and loaded """
class Doc:
    def __init__(self,id):
        self.__dict__={}
        self.__dict__['id'] = id
        #self.__dict__['lang'] = id.split(":")[-2]
        self.__dict__['raw'] = cache.fetchUrl(EURLEXURL+id).decode('utf-8')
        self.__dict__['refs'] = {}
        if getDict("db/"+self.id,create=False):
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

    def gettokenfreq(self):
        return map(
            lambda x: (x[0],len(x[1])),
            sorted(self.wpos.items(),
                   lambda x,y: cmp(len(x),len(y)),
                   itemgetter(1),
                   reverse=True))

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

    def getstemfreq(self):
        return map(
            lambda x: (x[0],len(x[1])),
            sorted(filter(lambda x: x[0],
                          self.spos.items()),
                   lambda x,y: cmp(len(x),len(y)),
                   itemgetter(1),
                   reverse=True))

    def addRef(self,stem,match,ref):
        if not self.refs.has_key(stem): self.refs[stem]={'matches':[],'refs':[]}
        if not match in self.refs[stem]['matches']:
            self.refs[stem]['matches'].append(match)
        if not ref.id in self.refs[stem]['refs']:
            self.refs[stem]['refs'].append(ref.id)

    def htmlRefs(self,docs):
        refs=sorted(self.refs.items(),
                    reverse=True,
                    cmp=lambda x,y: cmp(len(x[0]), len(y[0])))
        res=[]
        for (stem,ref) in refs:
            if len(stem) < 5: break
            columns=(int(100)/(len(ref['refs'])+1))
            res.append(u'<table class="frag" width="100%"><tr>')
            res.append(u'<td style="width:%d%%;">' % columns)
            res.append(htmlPippi(self.id,
                        ref['matches'],
                        self.getFrag(ref['matches'][0][0],ref['matches'][0][1])))
            res.append(u'</td>')
            for doc in ref['refs']:
                d=docs[doc]
                m=d.refs[stem]['matches']
                res.append(u'<td style="width:%d%%;">' % columns)
                res.append(htmlPippi(doc, m, d.getFrag(m[0][0],m[0][1])))
                res.append(u'</td>')
            res.append(u'</tr></table><hr />')
        return '\n'.join(res).encode('utf8')

    def getFrag(self,start,len):
        return " ".join(self.tokens[start:start+len]).encode('utf8')

    def save(self,dir="db/docs/"):
        dbdir=getDict(dir+"/"+self.id)
        for attr in ['text','tokens','stems','tokenfreq','stemfreq','refs','wpos','spos']:
            storeVal(dbdir+"/"+attr,cPickle.dumps(self.__getattr__(attr)))

    def load(self,dir="db/docs/"):
        dbdir=getDict(dir+"/"+self.id,create=False)
        if dbdir:
            for attr in ['text','tokens','stems','tokenfreq','stemfreq','refs','wpos','spos']:
                self.__dict__[attr]=cPickle.loads(loadVal(dbdir+"/"+attr))

    """ misc functions """
    def dumpRefs(self,docs):
        refs=sorted(self.refs.items(),reverse=True,cmp=lambda x,y: cmp(len(x[0]), len(y[0])))
        for (stem,ref) in refs:
            if len(stem) < 5: return
            print u"----- new frag -----\n>>",u"from",self.id+u":",ref['matches']
            print self.getFrag(ref['matches'][0][0],ref['matches'][0][1])
            for doc in ref['refs']:
                d=docs[doc]
                m=d.refs[stem]['matches']
                for f in m:
                    print u"\noccurs also in",doc,m,u"\n",d.getFrag(f[0],f[1])
            print

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

    def analyze(self,doc1,doc2):
        if doc1.id==doc2.id: return
        if doc1.id in self.docs.keys() and doc2.id in self.docs.keys(): return
        print u"analyzing",doc1.id,u"and",doc2.id
        matcher = difflib.SequenceMatcher(None,doc1.stems,doc2.stems)
        for match in matcher.get_matching_blocks():
            if not match[2]: continue
            m1=(match[0],match[2])
            m2=(match[1],match[2])
            stem=tuple(doc1.stems[match[0]:match[0]+match[2]])
            if not self.db.has_key(stem): self.db[stem]=[]
            if not (doc1.id,)+m1 in self.db[stem]: self.db[stem].append((doc1.id,)+m1)
            if not (doc2.id,)+m2 in self.db[stem]: self.db[stem].append((doc2.id,)+m2)
            doc1.addRef(stem,m1,doc2)
            doc2.addRef(stem,m2,doc1)

    def save(self,dir="db/"):
        for doc in self.docs.values():
            doc.save()
        storeVal(dir+"/matches",cPickle.dumps(self.db))

    def load(self,dir="db/"):
        try:
            self.db=cPickle.loads(loadVal(dir+"/matches")) or {}
        except:
            return
        for doc in os.listdir(dir+"/docs/"):
            d=Doc(doc)
            d.load()
            self.docs[doc]=d
        return True

    def longestFrags(self):
        return sorted(self.db.items(),
                      reverse=True,
                      cmp=lambda x,y: cmp(len(x[0]), len(y[0])))

    def htmlLongFrags(self):
        frags=self.longestFrags()
        res=[]
        for (k,docs) in frags:
            res.append(u'<table width="100%" class="frag"><tr>')
            for d in docs:
                res.append((u'<td style="width: %d%%;">' % (int(100)/len(docs))))
                res.append(htmlPippi(d[0],d[1:],self.docs[d[0]].getFrag(d[1],d[2])))
                res.append(u'</td>')
            res.append(u'</tr></table><hr />')
        return '\n'.join(res).encode('utf8')

    def addDoc(self,doc):
        if not self.docs.has_key(doc.id): self.docs[doc.id]=doc

    def insert(self,doc):
        if doc.id in self.docs.keys(): return
        for old in self.docs.values():
            self.analyze(newd,old)
        self.addDoc(doc)

    """ misc functions """
    def dump(self):
        return "%s\n%s" % (self.docs,self.db)

    def frequentFrags(self):
        return sorted(self.db.items(),
                      reverse=True,
                      cmp=lambda x,y: cmp(len(x[1]), len(y[1])))

    def stats(self):
        res="number of total common phrases: %d\n" % (len(self.db))
        res+="number of multigrams: %d\n" % (len(filter(lambda x: len(x)>2,self.db.keys())))
        res+="max len of frag: %d\n" % (len(self.longestFrags()[0][0]))
        return res

    def printLongFrags(self):
        frags=self.longestFrags()
        res=[]
        for (k,docs) in frags:
            for d in docs:
                res.append(u'%s: %s\n' % (d,self.docs[d[0]].getFrag(d[1],d[2])))
            res.append(u'-----\n')
        return '\n'.join(res).encode('utf8')

    def printFreqFrags(self):
        frags=self.frequentFrags()
        res=[]
        for (k,docs) in frags:
            if len(k)>1:
                res.append(u'%d\t%s' % (len(docs),k))
        return '\n'.join(res).encode('utf8')

    def printFreqTokens(self):
        frags=self.frequentFrags()
        res=[]
        for (k,docs) in frags:
            if len(k)==1:
                res.append(u'%d\t%s' % (len(docs),k))
        return '\n'.join(res).encode('utf8')


if __name__ == "__main__":
    db=MatchDb()
    print "loading..."
    db.load()
    print "done"
    print "---stats"
    print db.stats()
    print "---long frags"
    print db.printLongFrags()
    print "---frequent frags"
    print db.printFreqFrags()
    print "---frequent tokens"
    print db.printFreqTokens()
