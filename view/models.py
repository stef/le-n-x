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

from lenx.brain import cache as Cache
from django.conf import settings
DICTDIR=settings.DICT_PATH
from lenx.brain import cache as Cache
CACHE=Cache.Cache(settings.CACHE_PATH)

from django.db import models, connection
import platform
from lenx.brain import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?
from lenx.brain.dbutils import PickledObjectField, LockingManager

LANG='en_US'
DICT=DICTDIR+'/'+LANG
EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

class Frag(models.Model):
    frag = models.TextField()
    l = models.IntegerField()
    objects = LockingManager()
    @staticmethod
    def getFrag(stem):
      try:
         Frag.objects.lock()
         res, created = Frag.objects.get_or_create(frag=unicode(stem),l=len(stem))
         if created:
           res.save()
      finally:
         Frag.objects.unlock()
      return res

    def getStr(self):
        return " ".join(eval(self.frag)).encode('utf8')

    def __unicode__(self):
        return unicode(self.frag)+":"+unicode(self.l)+"\n"+unicode(self.doc_set.all())


""" class representing a distinct document, does stemming, some minimal nlp, can be saved and loaded """
class Doc(models.Model):
    eurlexid = models.CharField(unique=True,max_length=128)
    raw=PickledObjectField(default=None,null=True)
    text=PickledObjectField(default=None,null=True)
    tokens=PickledObjectField(default=None,null=True)
    stems=PickledObjectField(default=None,null=True)
    spos=PickledObjectField(default=None,null=True)
    wpos=PickledObjectField(default=None,null=True)
    title=models.TextField(default=None,max_length=8192,null=True)
    subject=models.CharField(default=None,max_length=512,null=True)
    frags = models.ManyToManyField(Frag, through='Location')
    objects = LockingManager()

    @staticmethod
    def getDoc(doc):
       try:
          Doc.objects.lock()
          res = Doc.objects.get(eurlexid=doc)
       except Doc.DoesNotExist:
          res = Doc.objects.create(eurlexid=doc)
          res.save()
       finally:
          Doc.objects.unlock()
       res.gettext()
       res.gettokens()
       res.getstems()
       res.gettitle()
       res.getsubj()
       res.save()
       return res

    def __unicode__(self):
        return self.eurlexid

    def gettext(self, cache=CACHE):
        if not self.text:
            self.raw = cache.fetchUrl(EURLEXURL+self.eurlexid)
            soup = BeautifulSoup(self.raw)
            # TexteOnly is the id used on eur-lex pages containing distinct docs
            self.text=[unicode(x) for x in soup.find(id='TexteOnly').findAll(text=True)]
        return self.text

    def gettokens(self):
        if not self.tokens:
            # start tokenizing
            self.tokens=[]
            self.wpos={}
            i=0
            for frag in self.gettext():
                if not frag: continue
                words=nltk.tokenize.wordpunct_tokenize(unicode(frag))
                self.tokens+=words
                # store positions of words
                for word in words:
                    self.wpos[word]=self.wpos.get(word,[])+[i]
                    i+=1
        return (self.tokens,self.wpos)

    def getstems(self):
        if not self.stems:
            # start stemming
            engine = hunspell.HunSpell(DICT+'.dic', DICT+'.aff')
            self.stems=[]
            self.spos={}
            i=0
            for word in self.gettokens()[0]:
                # stem each word and count the results
                stem=tuple(engine.stem(word.encode('utf8')))
                self.stems.append(stem)
                self.spos[stem]=self.spos.get(stem,[])+[i]
                i+=1
        return (self.stems,self.spos)

    def getFrag(self,start,len):
        return " ".join(self.gettokens()[0][start:start+len]).encode('utf8')

    def getMetaHTMLMetaData(self, attr, cache=CACHE):
        if not self.raw:
            self.raw = unicode(cache.fetchUrl(EURLEXURL+self.eurlexid),'utf-8')
        soup = BeautifulSoup(self.raw)
        res=map(lambda x: (x and x.has_key('content') and x['content']) or "",soup.findAll('meta',attrs={'name':attr}))
        return '|'.join(res).encode('utf-8')

    def gettitle(self, cache=CACHE):
        if not self.title:
            self.title=self.getMetaHTMLMetaData('DC.description')
        return self.title

    def getsubj(self, cache=CACHE):
        if not self.subject:
            self.subject=self.getMetaHTMLMetaData('DC.subject')
        return self.subject

class Location(models.Model):
    doc = models.ForeignKey(Doc)
    frag = models.ForeignKey(Frag)
    pos = models.IntegerField()
    txt = PickledObjectField()
    def __unicode__(self):
        return unicode(self.doc)+"@"+str(self.pos)+"\n"+self.txt
    @staticmethod
    def getLoc(doc,frag,pos,txt):
       try:
              Location.objects.lock()
              res = Location.objects.get(doc=doc,frag=frag,pos=pos,txt=txt)
       except Doc.DoesNotExist:
           try:
               res = Location.objects.create(doc=doc,frag=frag,pos=pos,txt=txt)
               res.save()
           finally:
               Location.objects.unlock()
       return res

