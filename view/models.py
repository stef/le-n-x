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
from brain import cache as Cache
CACHE=Cache.Cache('/home/stef/tasks/lenx/cache');

from django.db import models, connection
import platform
from brain import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?

LANG='en_US'
DICT=DICTDIR+'/'+LANG
EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

class LockingManager(models.Manager):
    def lock(self):
        """ Lock table.

        Locks the object model table so that atomic update is possible.
        Simulatenous database access request pend until the lock is unlock()'ed.

        Note: If you need to lock multiple tables, you need to do lock them
        all in one SQL clause and this function is not enough. To avoid
        dead lock, all tables must be locked in the same order.

        See http://dev.mysql.com/doc/refman/5.0/en/lock-tables.html
        """
        cursor = connection.cursor()
        table = self.model._meta.db_table
        #logger.debug("Locking table %s" % table)
        cursor.execute("LOCK TABLES %s WRITE" % table)
        row = cursor.fetchone()
        return row

    def unlock(self):
        """ Unlock the table. """
        cursor = connection.cursor()
        table = self.model._meta.db_table
        cursor.execute("UNLOCK TABLES")
        row = cursor.fetchone()
        return row

""" class representing a distinct document, does stemming, some minimal nlp, can be saved and loaded """
class Doc(models.Model):
    eurlexid = models.CharField(unique=True,max_length=128)
    raw=None
    text=None
    tokens=None
    stems=None
    spos=None
    wpos=None
    title=None
    subject=None
    objects = LockingManager()

    @staticmethod
    def getDoc(doc):
      try:
         Doc.objects.lock()
         res, created = Doc.objects.get_or_create(eurlexid=doc)
         if created:
           res.save()
      finally:
         Doc.objects.unlock()
      return res

    def __unicode__(self):
        return self.eurlexid

    def gettext(self, cache=CACHE):
        if not self.text:
            self.raw = cache.fetchUrl(EURLEXURL+self.eurlexid).decode('utf-8')
            soup = BeautifulSoup(self.raw)
            # TexteOnly is the id used on eur-lex pages containing distinct docs
            self.text=[unicode(x) for x in soup.find(id='TexteOnly').findAll(text=True)]
        return self.text

    def getMetaHTMLMetaData(self, attr, cache=CACHE):
        if not self.raw:
            self.raw = unicode(cache.fetchUrl(EURLEXURL+self.eurlexid),'utf-8')
        soup = BeautifulSoup(self.raw.encode('utf-8'))
        soup.findAll('meta',attrs={'name' :attr})
        res=map(lambda x: (x and x.has_key('content') and x['content']) or "",soup.findAll('meta',attrs={'name':attr}))
        return res

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

    def gettitle(self, cache=CACHE):
        if not self.title:
            self.title=self.getMetaHTMLMetaData('DC.description')
        return self.title

    def getsubj(self, cache=CACHE):
        if not self.subject:
            self.subject=self.getMetaHTMLMetaData('DC.subject')
        return self.title

class Location(models.Model):
    doc = models.ForeignKey(Doc)
    idx = models.IntegerField()
    txt = models.TextField()
    objects = LockingManager()
    @staticmethod
    def getLoc(doc,idx,l):
      txt=unicode(doc.gettokens()[0][idx:idx+l])
      try:
         Location.objects.lock()
         res, created = Location.objects.get_or_create(doc=doc,idx=idx,txt=txt)
         if created:
           res.save()
      finally:
         Location.objects.unlock()
      return res
    def __unicode__(self):
        return unicode(self.doc)+"@"+str(self.idx)+"\n"+self.txt

class Frag(models.Model):
    frag = models.TextField()
    l = models.IntegerField()
    docs = models.ManyToManyField(Location)
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
        return unicode(self.frag)+":"+unicode(self.l)+"\n"+unicode(self.docs.all())

