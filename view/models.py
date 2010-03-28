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

from django.conf import settings
DICTDIR=settings.DICT_PATH
from lenx.brain import cache as Cache
CACHE=Cache.Cache(settings.CACHE_PATH);

from django.db import models, connection
import platform
from lenx.brain import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?
from copy import deepcopy
from base64 import b64encode, b64decode
from zlib import compress, decompress
try:
    from cPickle import loads, dumps
except ImportError:
    from pickle import loads, dumps
from django.utils.encoding import force_unicode

LANG='en_US'
DICT=DICTDIR+'/'+LANG
EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

"""Pickle field implementation for Django. src:http://github.com/shrubberysoft/django-picklefield"""

class PickledObject(str):
    """
A subclass of string so it can be told whether a string is a pickled
object or not (if the object is an instance of this class then it must
[well, should] be a pickled one).

Only really useful for passing pre-encoded values to ``default``
with ``dbsafe_encode``, not that doing so is necessary. If you
remove PickledObject and its references, you won't be able to pass
in pre-encoded values anymore, but you can always just pass in the
python objects themselves.

"""


def dbsafe_encode(value, compress_object=False):
    """
We use deepcopy() here to avoid a problem with cPickle, where dumps
can generate different character streams for same lookup value if
they are referenced differently.

The reason this is important is because we do all of our lookups as
simple string matches, thus the character streams must be the same
for the lookups to work properly. See tests.py for more information.
"""
    if not compress_object:
        value = b64encode(dumps(deepcopy(value)))
    else:
        value = b64encode(compress(dumps(deepcopy(value))))
    return PickledObject(value)


def dbsafe_decode(value, compress_object=False):
    if not compress_object:
        value = loads(b64decode(value))
    else:
        value = loads(decompress(b64decode(value)))
    return value


class PickledObjectField(models.Field):
    """
A field that will accept *any* python object and store it in the
database. PickledObjectField will optionally compress it's values if
declared with the keyword argument ``compress=True``.

Does not actually encode and compress ``None`` objects (although you
can still do lookups using None). This way, it is still possible to
use the ``isnull`` lookup type correctly. Because of this, the field
defaults to ``null=True``, as otherwise it wouldn't be able to store
None values since they aren't pickled and encoded.

"""
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.compress = kwargs.pop('compress', False)
        self.protocol = kwargs.pop('protocol', 2)
        kwargs.setdefault('null', True)
        kwargs.setdefault('editable', False)
        super(PickledObjectField, self).__init__(*args, **kwargs)

    def get_default(self):
        """
Returns the default value for this field.

The default implementation on models.Field calls force_unicode
on the default, which means you can't set arbitrary Python
objects as the default. To fix this, we just return the value
without calling force_unicode on it. Note that if you set a
callable as a default, the field will still call it. It will
*not* try to pickle and encode it.

"""
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default
        # If the field doesn't have a default, then we punt to models.Field.
        return super(PickledObjectField, self).get_default()

    def to_python(self, value):
        """
B64decode and unpickle the object, optionally decompressing it.

If an error is raised in de-pickling and we're sure the value is
a definite pickle, the error is allowed to propogate. If we
aren't sure if the value is a pickle or not, then we catch the
error and return the original value instead.

"""
        if value is not None:
            try:
                value = dbsafe_decode(value, self.compress)
            except:
                # If the value is a definite pickle; and an error is raised in
                # de-pickling it should be allowed to propogate.
                if isinstance(value, PickledObject):
                    raise
        return value

    def get_db_prep_value(self, value):
        """
Pickle and b64encode the object, optionally compressing it.

The pickling protocol is specified explicitly (by default 2),
rather than as -1 or HIGHEST_PROTOCOL, because we don't want the
protocol to change over time. If it did, ``exact`` and ``in``
lookups would likely fail, since pickle would now be generating
a different string.

"""
        if value is not None and not isinstance(value, PickledObject):
            # We call force_unicode here explicitly, so that the encoded string
            # isn't rejected by the postgresql_psycopg2 backend. Alternatively,
            # we could have just registered PickledObject with the psycopg
            # marshaller (telling it to store it like it would a string), but
            # since both of these methods result in the same value being stored,
            # doing things this way is much easier.
            value = force_unicode(dbsafe_encode(value, self.compress))
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def get_internal_type(self):
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type not in ['exact', 'in', 'isnull']:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)
        # The Field model already calls get_db_prep_value before doing the
        # actual lookup, so all we need to do is limit the lookup types.
        return super(PickledObjectField, self).get_db_prep_lookup(lookup_type, value)

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
    title=models.TextField(default=None,max_length=512,null=True)
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
    txt = models.TextField()
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

